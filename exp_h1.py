# 实验H1: TLS 终止 CA 指纹(跨沙箱对比)
import subprocess

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== httpbin.org cert (TLS 终止) ==")
print(run("echo | openssl s_client -connect httpbin.org:443 -servername httpbin.org 2>/dev/null | openssl x509 -noout -fingerprint -sha256 -subject -issuer -serial -dates"))
print("== CA 证书位置 ==")
print(run("ls -la /etc/ssl/certs/ 2>/dev/null | head -5; find / -name '*vercel*' -o -name '*proxy*ca*' 2>/dev/null | grep -v proc | head -10"))
print("== 环境变量中的凭据/CA ==")
print(run("env | grep -i -E 'ca|cert|key|token|secret|cred' | head -10"))
