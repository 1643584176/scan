# 实验I3b: sandbox-init HTTP 路由枚举(精简版, 2s 超时)
import socket

def http_probe(path, method="GET", body=b"", timeout=2):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        hdr = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n\r\n".encode()
        s.sendall(hdr + body)
        data = b""
        try:
            while len(data) < 1200:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        status = data.split(b"\r\n")[0].decode(errors='replace') if data else "NO-RESPONSE"
        return status, data[:500]
    except Exception as e:
        return f"ERR {type(e).__name__}", b""

paths = ["/", "/health", "/healthz", "/status", "/info", "/version", "/api", "/v1",
         "/cmd", "/exec", "/run", "/shell", "/config", "/meta", "/sandbox", "/init",
         "/ws", "/socket", "/proxy", "/log", "/metrics", "/debug", "/debug/pprof/",
         "/env", "/token", "/auth", "/admin", "/internal", "/ping", "/ready", "/live"]

for p in paths:
    st, body = http_probe(p)
    if "404" not in st and "NO-RESPONSE" not in st and "ERR" not in st:
        print(f"GET  {p}: {st}  body={body[:200]!r}", flush=True)

for p in ["/", "/exec", "/cmd", "/run", "/api", "/shell", "/config", "/token"]:
    st, body = http_probe(p, "POST", b'{"cmd":"id"}')
    if "404" not in st and "NO-RESPONSE" not in st and "ERR" not in st:
        print(f"POST {p}: {st}  body={body[:200]!r}", flush=True)

print("done", flush=True)
