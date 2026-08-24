# 实验F2: deny-all/custom 模式下 ICMP + UDP 边界对比
import socket, subprocess, time

def run(cmd, timeout=12):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] ICMP ==")
for host in ["8.8.8.8", "1.1.1.1", "169.254.169.254"]:
    print(f"  ping {host}:", run(f"ping -c 2 -W 2 {host} 2>&1 | tail -2").replace(chr(10), " | "))

print("== [2] ICMP payload echo (外带通道 PoC) ==")
# 自定义 payload 到 8.8.8.8, 看 echo reply 是否回显
print(run("ping -c 1 -W 3 -p 414243444546 8.8.8.8 2>&1 | head -3"))

print("== [3] UDP ==")
def udp_probe(host, port, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.sendto(b"ABCDEFGH", (host, port))
        try:
            d, _ = s.recvfrom(512)
            return f"RECV {d[:30]!r} ({time.time()-t0:.1f}s)"
        except socket.timeout:
            return f"TIMEOUT ({time.time()-t0:.1f}s)"
    except OSError as e:
        return f"ERR {type(e).__name__}:{e}"
    finally:
        s.close()

for host in ["8.8.8.8", "1.1.1.1", "172.31.0.2"]:
    for port in [53, 443]:
        print(f"  udp {host}:{port}:", udp_probe(host, port))

print("== [4] TCP 对照 ==")
for host in ["8.8.8.8", "172.31.0.2"]:
    s = socket.socket(); s.settimeout(4)
    try:
        s.connect((host, 53))
        print(f"  tcp {host}:53 OPEN")
    except Exception as e:
        print(f"  tcp {host}:53 {type(e).__name__}")
    finally:
        s.close()

print("== [5] raw socket ICMP 可用性 ==")
print(run("python3 -c \"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP); print('RAW-ICMP OK')\" 2>&1"))
