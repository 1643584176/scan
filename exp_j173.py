# 实验J173: mount能力边界 + 传播标志 + 新syscall补测
# 动机: j172 mount tmpfs成功(与j83"must be superuser"矛盾) -> 需确认mount能力矩阵
#       + mountinfo propagation 标志(shared=逃逸级) + uid_map(user ns层级)
#       + 补测 io_uring/clone3/openat2 (j172脚本bug未测)
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

NAME = "expj173"
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

# 阶段A: mountinfo传播标志 + user ns层级 + 挂载点清单
PA = r'''
import os
out = open("/tmp/d173a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()

# 1. mountinfo 全量 (关注 shared:/master: 传播标志)
with open("/proc/self/mountinfo") as f:
    lines = f.readlines()
p("mountinfo_lines", len(lines))
for ln in lines[:40]:
    parts = ln.split()
    # 格式: id parent major:minor root mount_point options optional_fields...
    opt = [x for x in parts if x.startswith(("shared:", "master:", "propagate_from:"))]
    p("MNT", parts[4], "opts", parts[5], "prop", opt)
p("...")

# 2. user ns 层级
for f in ["/proc/self/uid_map", "/proc/self/gid_map", "/proc/self/ns/user", "/proc/self/ns/mnt", "/proc/self/ns/pid"]:
    try:
        if f.endswith("map"):
            with open(f) as fh:
                p(f, fh.read().strip())
        else:
            p(f, os.readlink(f))
    except Exception as e:
        p(f, "err", repr(e))

# 3. 当前挂载点简表
with open("/proc/self/mounts") as f:
    for ln in f.readlines()[:20]:
        p("MOUNTS", ln.strip())
p("=== A_DONE")
out.close()
'''

# 阶段B: mount 能力矩阵 (tmpfs/proc/sysfs/overlay/bind-vda/bind-proc1root)
PB = r'''
import os, ctypes
out = open("/tmp/d173b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
def syscall(n, *args):
    r = libc.syscall(n, *args)
    return r, ctypes.get_errno()

MS_RDONLY=1; MS_BIND=4096; MS_NOSUID=2; MS_NODEV=4; MS_NOEXEC=8
def try_mount(src, dst, fstype, flags, label):
    r, e = syscall(165, src, dst, fstype, flags, b"")
    p(label, r, "errno", e, os.strerror(e) if e else "OK")

for d in ["/tmp/mm_tmp", "/tmp/mm_proc", "/tmp/mm_sys", "/tmp/mm_ovl", "/tmp/mm_vda", "/tmp/mm_p1r", "/tmp/mm_p1m"]:
    try: os.makedirs(d, exist_ok=True)
    except Exception: pass

try_mount(b"none", b"/tmp/mm_tmp", b"tmpfs", 0, "m_tmpfs")
try_mount(b"none", b"/tmp/mm_proc", b"proc", 0, "m_proc")
try_mount(b"none", b"/tmp/mm_sys", b"sysfs", 0, "m_sysfs")
try_mount(b"none", b"/tmp/mm_ovl", b"overlay", 0, "m_overlay_noargs")
try_mount(b"/dev/vda", b"/tmp/mm_vda", b"xfs", MS_RDONLY, "m_vda_xfs")
try_mount(b"/", b"/tmp/mm_tmp", b"", MS_BIND, "m_bind_root")
# bind 到 /proc/1/root 下 (PID1与沙箱同mount ns, j100; 验证可写性)
try:
    os.makedirs("/proc/1/root/tmp/mm_p1m", exist_ok=True)
    r, e = syscall(165, b"/tmp/mm_tmp", b"/proc/1/root/tmp/mm_p1m", b"", MS_BIND, b"")
    p("m_bind_into_p1root", r, "errno", e, os.strerror(e) if e else "OK")
except Exception as ex:
    p("m_bind_into_p1root_exc", repr(ex))
p("=== B_DONE")
out.close()
'''

# 阶段C: 补测 io_uring/clone3/openat2/unshare/mount_setattr
PC = r'''
import os, ctypes
out = open("/tmp/d173c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
def syscall(n, *args):
    r = libc.syscall(n, *args)
    return r, ctypes.get_errno()

# io_uring_setup #425 (entries, flags)
r, e = syscall(425, 8, 0)
p("io_uring_setup", r, "errno", e, os.strerror(e) if e else "OK")
if r >= 0: os.close(r)

# clone3 #435 (NULL, 0) -> 预期EFAULT(14)表示seccomp放行; SIGSYS=被杀
r, e = syscall(435, 0, 0)
p("clone3", r, "errno", e, os.strerror(e) if e else "OK")

# openat2 #437 (dirfd=-100=AT_FDCWD, path, NULL, 0) -> EFAULT放行 / EPERM禁
r, e = syscall(437, -100, b"/etc/hostname", 0, 0)
p("openat2", r, "errno", e, os.strerror(e) if e else "OK")
if r >= 0: os.close(r)

# unshare #272 (0) 对照
r, e = syscall(272, 0)
p("unshare0", r, "errno", e, os.strerror(e) if e else "OK")

# mount_setattr #442 (未知面)
r, e = syscall(442, -100, b"/", 0, 0, 0)
p("mount_setattr", r, "errno", e, os.strerror(e) if e else "OK")

# keyctl #250 (KEYCTL_GET_KEYRING_ID=0, KEY_SPEC_PROCESS_KEYRING=-2)
r, e = syscall(250, 0, -2, 0)
p("keyctl_getring", r, "errno", e, os.strerror(e) if e else "OK")
p("=== C_DONE")
out.close()
'''

steps = [
    ("mountinfo", "/tmp/d173a.txt", PA),
    ("mount-matrix", "/tmp/d173b.txt", PB),
    ("syscall-probe", "/tmp/d173c.txt", PC),
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
