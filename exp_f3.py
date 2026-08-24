# 实验F3: custom 模式(允许httpbin.org)下 ICMP 边界
# 关键: ICMP 是否按 allowedDomains 过滤?
import socket, subprocess

def run(cmd, timeout=12):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== httpbin.org 解析 IP ==")
print(run("getent ahosts httpbin.org | head -3"))
print(run("getent ahosts 8.8.8.8 2>&1 | head -2"))

print("== [1] ICMP 到非允许域 IP ==")
print("ping 8.8.8.8:", run("ping -c 2 -W 2 8.8.8.8 2>&1 | tail -2").replace(chr(10), " | "))

print("== [2] ICMP 到允许域 IP ==")
print(run("for ip in $(getent ahosts httpbin.org | awk '{print $1}' | sort -u | head -2); do echo -n \"ping $ip: \"; ping -c 1 -W 2 $ip 2>&1 | tail -1; done"))

print("== [3] ICMP 到网关/链路 ==")
print("ping 100.64.0.1:", run("ping -c 1 -W 2 100.64.0.1 2>&1 | tail -1"))
print("ping 169.254.169.254:", run("ping -c 1 -W 2 169.254.169.254 2>&1 | tail -1"))

print("== [4] UDP 到允许域 IP ==")
def udp_probe(host, port, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(b"ABC", (host, port))
        try:
            d, _ = s.recvfrom(512)
            return f"RECV {d[:30]!r}"
        except socket.timeout:
            return "TIMEOUT"
    except OSError as e:
        return f"ERR {e}"
    finally:
        s.close()

import time
try:
    ip = run("getent ahosts httpbin.org | awk 'NR==1{print $1}'").strip()
except Exception:
    ip = "3.220.96.35"
print(f"udp {ip}:53:", udp_probe(ip, 53))
print(f"udp {ip}:443:", udp_probe(ip, 443))

print("== [5] ICMP echo reply payload 回显(自定义 payload) ==")
print(run("ping -c 1 -W 3 -p 4d41474943 8.8.8.8 2>&1 | head -4") if False else "skip(deny-all 已拒)")
