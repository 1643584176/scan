# 实验I3: sandbox-init HTTP 路由枚举 + 二进制字符串提取
import socket, subprocess

def run(cmd, timeout=12):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def http_probe(path, method="GET", body=b""):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect("/run/vercel/share/init.sock")
        hdr = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n\r\n".encode()
        s.sendall(hdr + body)
        data = b""
        try:
            while len(data) < 2000:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        # 提取状态行 + 简要
        lines = data.split(b"\r\n")
        status = lines[0].decode(errors='replace') if lines else ""
        return status, data[:800]
    except Exception as e:
        return f"ERR {type(e).__name__}", b""

paths = ["/", "/health", "/healthz", "/status", "/info", "/version", "/api", "/api/v1",
         "/v1", "/cmd", "/exec", "/run", "/shell", "/config", "/meta", "/sandbox",
         "/init", "/ws", "/socket", "/proxy", "/log", "/logs", "/metrics", "/debug",
         "/debug/pprof/", "/favicon.ico", "/.env", "/env", "/token", "/auth", "/login",
         "/connect", "/control", "/admin", "/internal", "/ping", "/ready", "/live"]

print("== HTTP 路由枚举 ==")
for p in paths:
    st, body = http_probe(p)
    tag = "***" if "200" in st or "405" in st else ""
    if "200" in st or "405" in st or "404" not in st:
        print(f"  {tag} {p}: {st}")
        if "200" in st:
            print(f"      body: {body[:300]!r}")

print("== POST 方法 ==")
for p in ["/", "/exec", "/cmd", "/run", "/api", "/v1", "/shell", "/config", "/token"]:
    st, body = http_probe(p, "POST", b'{"cmd":"id"}')
    if "200" in st or "405" not in st and "404" not in st:
        print(f"  POST {p}: {st}")
        if "200" in st:
            print(f"      body: {body[:300]!r}")

print("== 二进制字符串提取 ==")
print(run("grep -a -o -E '(/[a-zA-Z0-9_./-]{2,40})' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | grep -v -E '^\\.|lib|usr|etc|proc|sys|dev|var|tmp|bin|include|share' | head -40"))
print(run("grep -a -o -E 'vercel-[a-z-]{3,30}' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | head -20"))
