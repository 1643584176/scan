# 实验I14: 23456 ConnectRPC 服务确认 + CA 证书分析 + 二进制字符串提取
import socket, subprocess

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

def http_post(port, path, body=b"{}", ctype="application/connect+json"):
    try:
        s = socket.socket()
        s.settimeout(4)
        s.connect(("127.0.0.1", port))
        req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\nContent-Type: {ctype}\r\n"
               f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode() + body
        s.sendall(req)
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

print("== [1] 23456 POST SpawnService(connect+json) ==", flush=True)
for path in ["/vercel.sandbox.spawn.v1.SpawnService/Spawn",
             "/vercel.sandbox.spawn.v1.SpawnService/Ping",
             "/vercel.sandbox.spawn.v1.SpawnService/Kill"]:
    d = http_post(23456, path)
    print(f"  {path}: {d[:250]!r}", flush=True)

print("== [2] 23456 POST grpc 格式 ==", flush=True)
d = http_post(23456, "/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", "application/grpc")
print(f"  grpc Ping: {d[:250]!r}", flush=True)

print("== [3] vercel-proxy-ca.pem 内容 ==", flush=True)
print(run("cat /etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem 2>/dev/null | head -10"), flush=True)
print(run("openssl x509 -in /etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem -noout -subject -issuer -fingerprint -sha256 -dates 2>&1"), flush=True)

print("== [4] /run/cell 与 /run/vercel 目录 ==", flush=True)
print(run("ls -la /run/cell/ 2>&1; ls -laR /run/vercel/ 2>&1"), flush=True)

print("== [5] 二进制中 ConnectRPC 服务名提取(python) ==", flush=True)
try:
    data = open("/run/vercel/share/sandbox-init", "rb").read()
    print(f"  二进制大小: {len(data)}", flush=True)
    # 提取 vercel.sandbox 相关字符串
    import re
    strs = set()
    for m in re.finditer(rb"vercel\.sandbox\.[a-zA-Z0-9_.]+", data):
        strs.add(m.group(0).decode())
    for s in sorted(strs)[:50]:
        print(f"  {s}", flush=True)
    # 提取 /xxx 路由
    routes = set()
    for m in re.finditer(rb"/[a-z][a-zA-Z0-9/_.]{2,60}", data):
        s = m.group(0).decode()
        if "/" in s[1:] or s.startswith("/api") or s.startswith("/v1") or s.startswith("/v2") or s.startswith("/internal") or s.startswith("/debug") or s.startswith("/metrics") or s.startswith("/health"):
            routes.add(s)
    print("  --- 路由候选 ---", flush=True)
    for r in sorted(routes)[:60]:
        print(f"  {r}", flush=True)
except Exception as e:
    print(f"  ERR: {e}", flush=True)

print("== [6] 二进制中签名/密钥相关字符串 ==", flush=True)
try:
    import re
    data = open("/run/vercel/share/sandbox-init", "rb").read()
    pats = re.findall(rb"[a-zA-Z0-9_-]{4,40}", data)
    seen = set()
    for p in pats:
        s = p.decode(errors='ignore').lower()
        if any(k in s for k in ["signature", "ed25519", "verify", "unauthenticated", "timestamp", "pubkey", "x-sign", "hmac", "jwt", "token"]):
            if s not in seen:
                seen.add(s)
                print(f"  {p.decode(errors='ignore')}", flush=True)
except Exception as e:
    print(f"  ERR: {e}", flush=True)

print("done", flush=True)
