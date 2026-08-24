# 实验G4: 沙箱内请求 api.vercel.com/v2/user -> 匹配规则 -> 转发到 httpbin.org/anything
# 观察: 转发是否生效 + OIDC token 是否附加在转发的请求头中(httpbin 回显所有头)
import urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://api.vercel.com/v2/user"
req = urllib.request.Request(url)
try:
    r = urllib.request.urlopen(req, context=ctx, timeout=30)
    body = r.read(3000).decode(errors='replace')
    print("STATUS:", r.status)
    print("BODY:", body[:2000])
except urllib.error.HTTPError as e:
    body = e.read(2000)
    print("HTTPError:", e.code)
    print("BODY:", body[:1500])
except Exception as e:
    print("EXC:", type(e).__name__, e)
