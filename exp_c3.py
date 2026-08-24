import subprocess

def run(cmd, timeout=12):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return f"rc={r.returncode}\nOUT={r.stdout[:500]}\nERR={r.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERR {e}"

# 1. 看 10.0.0.1:443 的证书 CN/issuer(判断是 example.com 还是别的服务)
print("===== 1: 10.0.0.1:443 cert =====")
print(run("echo | timeout 10 openssl s_client -connect 10.0.0.1:443 -servername example.com 2>/dev/null | openssl x509 -noout -subject -issuer 2>/dev/null || echo no-cert"))

# 2. 看 1.1.1.1:443 的证书(SNI=example.com)
print("===== 2: 1.1.1.1:443 cert (sni=example.com) =====")
print(run("echo | timeout 10 openssl s_client -connect 1.1.1.1:443 -servername example.com 2>/dev/null | openssl x509 -noout -subject -issuer 2>/dev/null || echo no-cert"))

# 3. 内部网段可达性:100.64.0.0/10 内多个地址的 TCP 443
for ip in ["100.64.0.1", "100.64.1.154", "100.64.0.2", "100.127.255.254"]:
    print(f"===== 3: {ip}:443 =====")
    print(run(f"curl -sv --max-time 5 --resolve example.com:443:{ip} https://example.com/ 2>&1 | grep -E 'Trying|Connected|error|timed|refused|reset|Certificate' | head -5"))

# 4. 其他私有段
for ip in ["172.16.0.1", "192.168.0.1", "10.0.0.2", "10.1.0.1"]:
    print(f"===== 4: {ip}:443 =====")
    print(run(f"curl -sv --max-time 5 --resolve example.com:443:{ip} https://example.com/ 2>&1 | grep -E 'Trying|Connected|error|timed|refused|reset|Certificate' | head -5"))
