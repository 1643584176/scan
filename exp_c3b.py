import subprocess, socket, time

def run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return f"rc={r.returncode} OUT={r.stdout[:300]!r} ERR={r.stderr[:150]!r}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERR {e}"

# 1. 1.1.1.1:443 证书(SNI=example.com)——确认到达 Cloudflare
print("[1] 1.1.1.1 cert:", run("echo | timeout 6 openssl s_client -connect 1.1.1.1:443 -servername example.com 2>/dev/null | openssl x509 -noout -subject -issuer 2>/dev/null || echo NO-CERT"))

# 2. 10.0.0.1:443 证书——确认是什么服务
print("[2] 10.0.0.1 cert:", run("echo | timeout 6 openssl s_client -connect 10.0.0.1:443 -servername example.com 2>/dev/null | openssl x509 -noout -subject -issuer 2>/dev/null || echo NO-CERT"))

# 3. 100.64.x 内部网段探测(TCP connect 测试)
def tcp_probe(ip, port=443, timeout=4):
    s = socket.socket()
    s.settimeout(timeout)
    t0=time.time()
    try:
        s.connect((ip, port))
        s.close()
        return f"OPEN {time.time()-t0:.2f}s"
    except socket.timeout:
        return "TIMEOUT"
    except Exception as e:
        return f"CLOSED {e}"
    finally:
        s.close()

for ip in ["100.64.0.1", "100.64.0.2", "100.64.1.154", "100.127.255.254", "100.64.1.1", "100.65.0.1"]:
    print(f"[3] {ip}:443", tcp_probe(ip))

# 4. 其他私有段
for ip in ["172.16.0.1", "172.17.0.1", "192.168.0.1", "192.168.1.1", "10.0.0.1", "10.0.0.2", "10.1.0.1", "10.10.0.1"]:
    print(f"[4] {ip}:443", tcp_probe(ip))
