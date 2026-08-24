# 实验J94b: 宿主 TCP 服务协议指纹 — 30001/30002/23456 用 ssl/HTTP/h2 preface 探测
import json, time, urllib.request, urllib.error, sys, base64, socket, ssl
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

NAME = "expj94b"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import socket, ssl

PORTS = [30001, 30002, 23456]

def tcp_send(port, payload, label, timeout=4):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(payload)
        data = b""
        try:
            while len(data) < 600:
                chunk = s.recv(600 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        return f"{label}: resp({len(data)}B) {data[:150]!r}"
    except Exception as e:
        return f"{label}: ERR({e})"

def tls_probe(port, sni="localhost", timeout=4):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.settimeout(timeout)
        t = ctx.wrap_socket(s, server_hostname=sni)
        # 尝试发 HTTP 请求
        t.sendall(b"GET / HTTP/1.1\r\nHost: " + sni.encode() + b"\r\n\r\n")
        data = b""
        try:
            while len(data) < 600:
                chunk = t.recv(600 - len(data))
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        ver = t.version()
        t.close()
        return f"TLS-OK({ver}) resp({len(data)}B) {data[:150]!r}"
    except ssl.SSLError as e:
        return f"TLS-SSLERR({e})"
    except Exception as e:
        return f"TLS-ERR({e})"

for port in PORTS:
    print(f"--- port {port} ---", flush=True)
    print("  ", tcp_send(port, b"GET / HTTP/1.1\r\nHost: x\r\n\r\n", "http"), flush=True)
    print("  ", tcp_send(port, b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n", "h2"), flush=True)
    print("  ", tcp_send(port, b"hello\x00", "raw"), flush=True)
    print("  ", tls_probe(port), flush=True)

# 尝试 gRPC health check (如果 h2 preface 有响应)
print("== gRPC health on 30002 (http2 client) ==", flush=True)
try:
    import http.client
    # 用 http.client 无法发 h2; 直接发 gRPC framing 到 30002
    s = socket.create_connection(("127.0.0.1", 30002), timeout=4)
    s.settimeout(4)
    # HTTP/2 preface + SETTINGS frame
    settings = b"\x00\x00\x00\x04\x00\x00\x00\x00\x00"
    s.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n" + settings)
    data = b""
    try:
        while len(data) < 400:
            chunk = s.recv(400 - len(data))
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    print("  h2 settings resp:", repr(data[:200]), flush=True)
    s.close()
except Exception as e:
    print("  ERR", e, flush=True)
"""
run_cmd(sid, PROBE, "tcp-fingerprint", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
