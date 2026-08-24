# -*- coding: utf-8 -*-
"""实验J268: 验证"持续输出保持命令存活"假说
A: 每 0.3 秒 print "." 持续 12 秒 (若活到 OK_A -> 假说成立)
B: print 一次后 sleep 5 (对照: 无输出 -> 应被杀)
C: 心跳 + 同时 h2 connect init.sock send Ping (免签对照, patch 前)
"""
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
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    dt = time.time() - t0
    print(f"=== cmd[{label}] status {c} wall={dt:.1f}s ===", flush=True)
    out = ""
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
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    if out:
        print(out, flush=True)
    return out

NAME = "expj268"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: 心跳输出 0.3s 间隔, 12 秒
CODE_A = r'''
import time
t0 = time.time()
while time.time() - t0 < 12:
    print(".", end="", flush=True)
    time.sleep(0.3)
print("\nOK_A", flush=True)
'''
rA = run_cmd(sid, CODE_A, "A_HEARTBEAT", timeout=100)
print("A done:", "OK_A" in (rA or ""), "bytes:", len(rA or ""), flush=True)

# B: 无输出 sleep 5 (对照)
CODE_B = r'''
import time
time.sleep(5)
print("OK_B", flush=True)
'''
rB = run_cmd(sid, CODE_B, "B_NOSLEEP", timeout=100)
print("B done:", "OK_B" in (rB or ""), flush=True)

# C: 心跳 + h2 connect init.sock + send Ping (patch 前对照)
CODE_C = r'''
import socket, struct, base64, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
t0 = time.time()
def hb():
    print("hb%.1f " % (time.time() - t0), end="", flush=True)

# 心跳线程
import threading
def hb_loop():
    while True:
        time.sleep(0.4)
        print("h", end="", flush=True)
threading.Thread(target=hb_loop, daemon=True).start()

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect("/run/vercel/share/init.sock")
p("\nC connected", flush=True)
sock.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
def fr(t, flags, sid, payload):
    return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
sock.sendall(fr(4, 0, 0, b""))
headers = (
    b":method: POST\r\n:scheme: http\r\n:path: /vercel.sandbox.spawn.v1.SpawnService/Ping\r\n"
    b":authority: init\r\ncontent-type: application/json\r\nconnect-protocol-version: 1\r\n"
    b"content-length: 2\r\n"
)
hp = base64.b64encode(headers)
sock.sendall(fr(1, 0x4, 1, b"\x00" + hp))
sock.sendall(fr(0, 0x1, 1, b"{}"))
p("C sent", flush=True)
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
    p("\nC TIMEOUT after", len(data), flush=True)
except Exception as e:
    p("\nC READ_ERR", type(e).__name__, str(e)[:80], flush=True)
p("\nC_RESP", len(data), flush=True)
asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
p("C_ASC", asc[:400], flush=True)
print("\nOK_C", flush=True)
'''
rC = run_cmd(sid, CODE_C, "C_H2PING", timeout=100)
print("C done:", "OK_C" in (rC or ""), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
