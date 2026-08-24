# 实验B验证: transform 凭据注入是否生效
# 1) 证书oracle: httpbin.org(有transform) 应显示 Vercel CA 证书, example.com(无transform) 真实证书
# 2) echo oracle: httpbin.org/headers 回显请求头, 验证注入头是否真实到达目标
import subprocess, urllib.request, sys

def cert_issuer(host, port=443):
    r = subprocess.run(["openssl", "s_client", "-connect", f"{host}:{port}",
                        "-servername", host, "-brief"],
                       input=b"", capture_output=True, timeout=12)
    out = (r.stdout + r.stderr).decode(errors='replace')
    for line in out.splitlines():
        if "issuer" in line or "Verify return code" in line or "Protocol" in line:
            return line.strip()
    return "NO-ISSUER-LINE: " + out[:300]

def echo_headers():
    req = urllib.request.Request("https://httpbin.org/headers")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode(errors='replace')[:800]

print("== [1] cert example.com (无transform) ==")
try:
    print("   issuer:", cert_issuer("example.com"))
except Exception as e:
    print("   ERR", type(e).__name__, e)

print("== [2] cert httpbin.org (有transform) ==")
try:
    print("   issuer:", cert_issuer("httpbin.org"))
except Exception as e:
    print("   ERR", type(e).__name__, e)

print("== [3] echo headers (httpbin.org/headers) ==")
try:
    print(echo_headers())
except Exception as e:
    print("   ERR", type(e).__name__, e)
