# 实验J95: 宿主内部服务路径枚举 + Connect/gRPC RPC 探测 (30001/23456)
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
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
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

NAME = "expj95"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import socket

PORTS = [30001, 23456]

PATHS = [
    "/", "/health", "/healthz", "/readyz", "/livez", "/ping", "/version",
    "/metrics", "/debug/pprof/", "/debug/vars", "/api", "/api/v1",
    "/v1", "/v1/health", "/status", "/info", "/sandbox", "/sandboxes",
    "/session", "/sessions", "/cell", "/run", "/vercel", "/version.json",
]

def req(port, path, headers=b"", timeout=3):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"GET " + path.encode() + b" HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n" + headers + b"\r\n")
        data = b""
        try:
            while len(data) < 500:
                chunk = s.recv(500 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        status = data.split(b"\r\n", 1)[0] if data else b"NO-RESP"
        body = data.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in data else b""
        return status.decode(errors="replace"), body[:120]
    except Exception as e:
        return f"ERR({e})", b""

for port in PORTS:
    print(f"===== port {port} =====", flush=True)
    for p in PATHS:
        st, body = req(port, p)
        if "404" not in st and "ERR" not in st:
            print(f"  [{p}] {st} body={body!r}", flush=True)
        elif "ERR" in st:
            print(f"  [{p}] {st}", flush=True)
    # Connect RPC 探测 (仿 init.sock 风格)
    print("--- Connect RPC probe ---", flush=True)
    for path in ["/vercel.sandbox.v1.SandboxService/Health", "/vercel.cell.v1.CellService/Health",
                 "/grpc.health.v1.Health/Check", "/cell.v1.CellService/Health",
                 "/vercel.cell.v1.CellService/Ping"]:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=3)
            s.settimeout(3)
            body = b"\x00\x00\x00\x00\x02"
            s.sendall(b"POST " + path.encode() + b" HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/connect+json\r\nConnect-Protocol-Version: 1\r\nContent-Length: 5\r\n\r\n" + body)
            data = b""
            try:
                while len(data) < 500:
                    chunk = s.recv(500 - len(data))
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass
            s.close()
            st = data.split(b"\r\n", 1)[0] if data else b"NO-RESP"
            print(f"  [{path}] {st.decode(errors='replace')} body={data[-150:]!r}", flush=True)
        except Exception as e:
            print(f"  [{path}] ERR({e})", flush=True)
"""
run_cmd(sid, PROBE, "host-path-enum", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
