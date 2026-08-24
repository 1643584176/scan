# 实验G4b: 转发机制确认 + OIDC token 附加观察(重试3次 + 两种目标)
import urllib.request, ssl, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://api.vercel.com/v2/user"
for i in range(3):
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, context=ctx, timeout=30)
        body = r.read(4000).decode(errors='replace')
        print(f"== 尝试{i+1} STATUS {r.status}", flush=True)
        print("HEADERS:", dict(r.headers)[:800] if False else {k: v for k, v in r.headers.items()}, flush=True)
        print("BODY:", body[:2500], flush=True)
    except urllib.error.HTTPError as e:
        print(f"== 尝试{i+1} HTTPError {e.code}", flush=True)
        print("HEADERS:", {k: v for k, v in e.headers.items()}, flush=True)
        print("BODY:", e.read(2000)[:1500], flush=True)
    except Exception as e:
        print(f"== 尝试{i+1} EXC {type(e).__name__}: {e}", flush=True)
    time.sleep(1)
