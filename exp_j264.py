# -*- coding: utf-8 -*-
"""实验J264: 区分被杀触发条件
E1: 纯 sleep 45 (TTL 测试 - 无操作是否被杀)
E2: connect init.sock 不发数据 + sleep 20
E3: connect + 发 5 字节垃圾 + sleep 20
E4: connect + HTTP/1.1 无签名 POST Ping (已知会被杀?)
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

NAME = "expj264"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# E1: 纯 sleep 45 (无任何 socket 操作)
CODE_1 = r'''
import time
print("E1 start", flush=True)
time.sleep(45)
print("E1_DONE alive", flush=True)
'''
r1 = run_cmd(sid, CODE_1, "E1_SLEEP", timeout=120)
if "E1_DONE" in (r1 or ""):
    print("\n-> E1 alive: TTL > 45s, 继续 E2", flush=True)
    CODE_2 = r'''
import socket, time
print("E2 start", flush=True)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/run/vercel/share/init.sock")
print("E2 connected, no data", flush=True)
time.sleep(20)
print("E2_DONE alive", flush=True)
'''
    r2 = run_cmd(sid, CODE_2, "E2_CONNECT", timeout=120)
    if "E2_DONE" in (r2 or ""):
        print("\n-> E2 alive: 连接不发数据安全, 继续 E3", flush=True)
        CODE_3 = r'''
import socket, time
print("E3 start", flush=True)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/run/vercel/share/init.sock")
s.sendall(b"HELLO")
print("E3 sent garbage", flush=True)
time.sleep(20)
print("E3_DONE alive", flush=True)
'''
        r3 = run_cmd(sid, CODE_3, "E3_GARBAGE", timeout=120)
        if "E3_DONE" in (r3 or ""):
            print("\n-> E3 alive: 垃圾数据安全, 继续 E4 (HTTP/1.1 无签名)", flush=True)
            CODE_4 = r'''
import socket, time
print("E4 start", flush=True)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(8)
s.connect("/run/vercel/share/init.sock")
req = (
    b"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\n"
    b"Host: init\r\nContent-Type: application/json\r\n"
    b"Content-Length: 2\r\nConnect-Protocol-Version: 1\r\n\r\n{}"
)
s.sendall(req)
print("E4 sent http ping", flush=True)
try:
    d = s.recv(4096)
    print("E4 recv", len(d), repr(d[:200]), flush=True)
except Exception as e:
    print("E4 recv_err", type(e).__name__, str(e)[:80], flush=True)
time.sleep(10)
print("E4_DONE alive", flush=True)
'''
            r4 = run_cmd(sid, CODE_4, "E4_HTTP", timeout=120)
            print("E4 result contains DONE:", "E4_DONE" in (r4 or ""), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
