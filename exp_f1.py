# 实验F1: allow-all 默认策略下网络边界完整矩阵
# 1) httpbin.org 证书指纹(跨沙箱 CA 对比)
# 2) UDP 矩阵(8.8.8.8/1.1.1.1 x 53/443)
# 3) ICMP
# 4) MMDS 可达性
import socket, subprocess, time

def run(cmd, timeout=12):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] cert fingerprint ==")
print(run("echo | openssl s_client -connect httpbin.org:443 -servername httpbin.org 2>/dev/null | openssl x509 -noout -fingerprint -sha256 -subject -issuer"))

print("== [2] UDP matrix ==")
def udp_probe(host, port, payload=b"\x00\x01\x02\x03", timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.sendto(payload, (host, port))
        try:
            d, _ = s.recvfrom(512)
            return f"RECV {d[:40]!r} ({time.time()-t0:.1f}s)"
        except socket.timeout:
            return f"TIMEOUT no-reply ({time.time()-t0:.1f}s)"
    except OSError as e:
        return f"ERR {type(e).__name__}:{e}"
    finally:
        s.close()

for host in ["8.8.8.8", "1.1.1.1"]:
    for port in [53, 443, 12345]:
        print(f"  udp {host}:{port}:", udp_probe(host, port))

print("== [3] ICMP ==")
print(run("ping -c 2 -W 2 8.8.8.8 2>&1 | tail -3"))

print("== [4] MMDS ==")
print(run("curl -s -m 6 -o - -w '\\nHTTP:%{http_code}' http://169.254.169.254/latest/meta-data/ 2>&1 | head -c 300"))
print()
print(run("curl -s -m 6 -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' -o - -w '\\nHTTP:%{http_code}' 2>&1 | head -c 200"))
