# -*- coding: utf-8 -*-
"""实验J287q: 枚举 23456/30001/30002 端口路由 + gRPC reflection"""
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

NAME = "expj287q"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: 三端口路径枚举 (GET+POST 指纹)
out = run_cmd(sid, r'''
import socket, time
PORTS = [23456, 30001, 30002]
PATHS = ["/", "/healthz", "/health", "/status", "/ready", "/livez", "/metrics",
         "/version", "/info", "/debug/pprof/", "/debug/pprof/goroutine",
         "/v1/", "/v1/exec", "/v1/spawn", "/v2/", "/v2/exec", "/v2/spawn",
         "/exec", "/spawn", "/cmd", "/run", "/api", "/api/exec", "/api/fs",
         "/fs", "/files", "/upload", "/download", "/ws", "/socket",
         "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
         "/grpc.health.v1.Health/Check",
         "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo"]

def req(port, path, method):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        body = b"{}"
        if method == "POST":
            r = (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: init\r\n"
                 b"Content-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
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
                if len(data) > 3000:
                    break
        except socket.timeout:
            pass
        s.close()
        head = data.split(b"\r\n\r\n")[0].decode("latin1", "replace")
        line1 = head.split("\r\n")[0] if head else "NO_RESP"
        ct = [h for h in head.split("\r\n") if h.lower().startswith("content-type")][:1]
        return "%s %s" % (line1, ct[0] if ct else "")
    except Exception as e:
        return "EXC %s" % type(e).__name__

for p in PORTS:
    print("===== PORT %d =====" % p, flush=True)
    for path in PATHS:
        for m in ("GET", "POST"):
            print("%s %s -> %s" % (m, path, req(p, path, m)), flush=True)
        time.sleep(0.05)
print("ALLDONE", flush=True)
''', "ROUTE_ENUM", timeout=280)
print("ROUTE_ENUM out len:", len(out or ""), flush=True)
print((out or "")[:15000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
