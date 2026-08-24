# 实验I6: SpawnService 正确 Content-Type 调用 + 鉴权边界测绘
import socket, json

def connect_call(service_method, body=b"{}", ctype="application/connect+json", timeout=5, headers=None):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        hdr = (f"POST /{service_method} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: {ctype}\r\n"
               f"Content-Length: {len(body)}\r\n")
        if headers:
            for k, v in headers.items():
                hdr += f"{k}: {v}\r\n"
        hdr += "\r\n"
        s.sendall(hdr.encode() + body)
        data = b""
        try:
            while len(data) < 6000:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        return data[:2000]
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}".encode()

print("== [1] Spawn (connect+json, 空 body) ==")
print("  ", connect_call("vercel.sandbox.spawn.v1.SpawnService/Spawn", b"{}")[:500], flush=True)

print("== [2] Spawn command=id ==")
body = json.dumps({"command": "id", "args": [], "env": {}, "cwd": "/"}).encode()
print("  ", connect_call("vercel.sandbox.spawn.v1.SpawnService/Spawn", body)[:500], flush=True)

print("== [3] Spawn 变体字段 ==")
for b in [b'{"cmd":"id"}', b'{"executable":"id"}', b'{"argv":["id"]}', b'{"process":{"command":"id"}}',
          b'{"command":"/usr/bin/id","args":["-a"]}', b'{"command":"id","interactive":false}']:
    r = connect_call("vercel.sandbox.spawn.v1.SpawnService/Spawn", b)
    print(f"  {b.decode()}: {r[:300]!r}", flush=True)

print("== [4] Ping ==")
print("  ", connect_call("vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}")[:400], flush=True)

print("== [5] SpawnStarted / PtyStart / PtyResize ==")
for m in ["SpawnStarted", "PtyStart", "PtyResize"]:
    r = connect_call(f"vercel.sandbox.spawn.v1.SpawnService/{m}", b"{}")
    print(f"  {m}: {r[:300]!r}", flush=True)

print("== [6] Kill 带假签名头 ==")
r = connect_call("vercel.sandbox.spawn.v1.SpawnService/Kill", b"{}",
                 headers={"x-signature": "AA==", "x-signature-algorithm": "ed25519"})
print(f"  Kill: {r[:400]!r}", flush=True)

print("done", flush=True)
