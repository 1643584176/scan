# 实验I13: 23456 HTTP 服务路由枚举 + 二进制分析 + mount 隔离确认
import socket, subprocess, re

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

def http_get(port, path, host="localhost"):
    try:
        s = socket.socket()
        s.settimeout(4)
        s.connect(("127.0.0.1", port))
        req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        data = b""
        try:
            while True:
                c = s.recv(4096)
                if not c: break
                data += c
        except socket.timeout:
            pass
        s.close()
        return data
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}".encode()

print("== [1] 二进制字符串提取路由 ==", flush=True)
out = run("strings -n 6 /run/vercel/share/sandbox-init 2>/dev/null | grep -E '^/(api|v[0-9]|vercel|internal|debug|health|metrics|run|sandbox|spawn|pty|env|fs|exec)[a-zA-Z0-9/_.-]*$' | sort -u | head -60")
print(out, flush=True)

print("== [2] 更多路径模式(含 /vercel. 前缀) ==", flush=True)
out = run("strings -n 4 /run/vercel/share/sandbox-init 2>/dev/null | grep -E 'vercel\.(sandbox|agent|spawn|pty|env|fs|internal|control)' | sort -u | head -40")
print(out, flush=True)

print("== [3] 23456 常见路径探测 ==", flush=True)
paths = ["/", "/health", "/healthz", "/metrics", "/debug/pprof/", "/version", "/v1", "/v2",
         "/api", "/api/v1", "/vercel", "/sandbox", "/spawn", "/internal", "/run",
         "/env", "/exec", "/fs", "/pty", "/sandbox/spawn", "/v1/sandbox", "/v1/spawn",
         "/vercel.sandbox.spawn.v1.SpawnService", "/vercel.sandbox.spawn.v1.SpawnService/Spawn"]
for p in paths:
    d = http_get(23456, p)
    if isinstance(d, bytes):
        status = d.split(b"\r\n")[0].decode() if d else "EMPTY"
        body = d.split(b"\r\n\r\n", 1)[-1][:80] if b"\r\n\r\n" in d else b""
        print(f"  {p:55s} -> {status} | {body!r}", flush=True)
    else:
        print(f"  {p:55s} -> {d}", flush=True)

print("== [4] IPv6 本机端口 ==", flush=True)
for port in [7531, 7532, 23456]:
    try:
        s = socket.socket(socket.AF_INET6)
        s.settimeout(3)
        s.connect(("::1", port))
        s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        try:
            d = s.recv(200)
            print(f"  [::1]:{port} -> {d[:120]!r}", flush=True)
        except socket.timeout:
            print(f"  [::1]:{port} OPEN (无响应)", flush=True)
        s.close()
    except Exception as e:
        print(f"  [::1]:{port} -> {type(e).__name__}", flush=True)

print("== [5] mount 隔离(containerd.sock 可达性) ==", flush=True)
print(run("cat /proc/1/mountinfo 2>/dev/null | grep -iE 'run|containerd|vercel' | head -10"), flush=True)
print(run("mount 2>/dev/null | grep -E 'run|containerd|vercel' | head -10"), flush=True)
print(run("ls -la /run/ 2>/dev/null | head -20"), flush=True)

print("== [6] 二进制签名相关字符串 ==", flush=True)
out = run("strings -n 5 /run/vercel/share/sandbox-init 2>/dev/null | grep -iE 'signature|sign|ed25519|verify|unauthenticated|timestamp|pubkey' | sort -u | head -40")
print(out, flush=True)

print("done", flush=True)
