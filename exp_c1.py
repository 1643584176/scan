# 沙箱内执行: 请求 httpbin.org (SNI=httpbin.org, 有 forwardURL 规则)
# 期望响应包含 vercel-forwarded-* 头和 vercel-sandbox-oidc-token
import urllib.request, json

r = urllib.request.Request("https://httpbin.org/anything")
r.add_header("User-Agent", "exp-c1")
try:
    with urllib.request.urlopen(r, timeout=20) as resp:
        print("STATUS", resp.status)
        print(resp.read().decode(errors='replace')[:2500])
except Exception as e:
    print("ERR", type(e).__name__, e)
