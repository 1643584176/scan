# -*- coding: utf-8 -*-
"""实验J287t: 测23456/30001/30002是否HTTP代理(CONNECT/绝对URL) + 慢速路径枚举"""
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

NAME = "expj287t"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: 代理行为测试 (4请求, 间隔1s)
out = run_cmd(sid, r'''
import socket, time
def raw(port, payload, timeout=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(("127.0.0.1", port))
        s.sendall(payload)
        data = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 4000:
                    break
        except socket.timeout:
            pass
        s.close()
        return repr(data[:800])
    except Exception as e:
        return "EXC %s %s" % (type(e).__name__, e)

# 1. CONNECT 代理测试 23456
print("T1 CONNECT 23456:", raw(23456, b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n"), flush=True)
time.sleep(1)
# 2. 绝对 URL GET 23456 (正向代理)
print("T2 GET absurl 23456:", raw(23456, b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"), flush=True)
time.sleep(1)
# 3. CONNECT 30001
print("T3 CONNECT 30001:", raw(30001, b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n"), flush=True)
time.sleep(1)
# 4. CONNECT 30002
print("T4 CONNECT 30002:", raw(30002, b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n"), flush=True)
print("DONE", flush=True)
''', "PROXY", timeout=100)
print("PROXY out:", repr((out or "")[:2500]), flush=True)

# cmd2: 慢速路径枚举 23456 (10路径, 间隔0.8s)
out = run_cmd(sid, r'''
import socket, time
def req(port, path, method="GET", body=None):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        if method == "POST":
            b = body or b"{}"
            r = (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: init\r\n"
                 b"Content-Type: application/connect+json\r\nContent-Length: " + str(len(b)).encode() +
                 b"\r\nConnection: close\r\n\r\n" + b)
        else:
            r = (b"GET " + path.encode() + b" HTTP/1.1\r\nHost: init\r\nConnection: close\r\n\r\n")
        s.sendall(r)
        data = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 2500:
                    break
        except socket.timeout:
            pass
        s.close()
        return repr(data[:500])
    except Exception as e:
        return "EXC %s" % type(e).__name__
PATHS = ["/v1/proxy", "/v1/exec", "/v1/spawn", "/v1/logs", "/v1/events",
         "/v1/snapshot", "/v1/fs", "/v1/network", "/v1/health", "/v1/status"]
for p in PATHS:
    print("23456 GET %s: %s" % (p, req(23456, p)), flush=True)
    time.sleep(0.8)
print("DONE", flush=True)
''', "PATH1", timeout=280)
print("PATH1 out:", repr((out or "")[:2500]), flush=True)

# cmd3: 慢速路径枚举 30001 (10路径)
out = run_cmd(sid, r'''
import socket, time
def req(port, path, method="GET", body=None):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        if method == "POST":
            b = body or b"{}"
            r = (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: init\r\n"
                 b"Content-Type: application/connect+json\r\nContent-Length: " + str(len(b)).encode() +
                 b"\r\nConnection: close\r\n\r\n" + b)
        else:
            r = (b"GET " + path.encode() + b" HTTP/1.1\r\nHost: init\r\nConnection: close\r\n\r\n")
        s.sendall(r)
        data = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 2500:
                    break
        except socket.timeout:
            pass
        s.close()
        return repr(data[:500])
    except Exception as e:
        return "EXC %s" % type(e).__name__
PATHS = ["/v1/proxy", "/v1/exec", "/v1/spawn", "/v1/logs", "/v1/events",
         "/v1/snapshot", "/v1/fs", "/v1/network", "/v1/health", "/v1/status"]
for p in PATHS:
    print("30001 GET %s: %s" % (p, req(30001, p)), flush=True)
    time.sleep(0.8)
print("DONE", flush=True)
''', "PATH2", timeout=280)
print("PATH2 out:", repr((out or "")[:2500]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
