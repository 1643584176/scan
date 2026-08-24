# I17-2: 沙箱内精简扫描脚本(只测目标端口 + 无签名 Spawn)
# 通过 TARGET_IP 环境变量传入目标沙箱 IP
import socket, os

target = os.environ.get("TARGET_IP", "")
print(f"== 扫描目标 {target} ==", flush=True)

print("-- 端口扫描 --", flush=True)
for port in [23456, 7531, 7532, 22, 80, 443, 47076, 2375, 2376]:
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((target, port))
        print(f"  *** {target}:{port} OPEN ***", flush=True)
        s.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        try:
            d = s.recv(120)
            print(f"     响应: {d[:120]!r}", flush=True)
        except socket.timeout:
            pass
        s.close()
    except Exception as e:
        print(f"  {target}:{port} CLOSED ({type(e).__name__})", flush=True)

print("-- 无签名 Spawn 调用 --", flush=True)
try:
    s = socket.socket()
    s.settimeout(3)
    s.connect((target, 23456))
    body = b"{}"
    req = (f"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\nHost: localhost\r\n"
           f"Content-Type: application/connect+json\r\nContent-Length: {len(body)}\r\n\r\n").encode() + body
    s.sendall(req)
    data = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            data += c
    except socket.timeout:
        pass
    print(f"  Spawn 无签名: {data[:200]!r}", flush=True)
    s.close()
except Exception as e:
    print(f"  Spawn: ERR {type(e).__name__}", flush=True)

print("done", flush=True)
