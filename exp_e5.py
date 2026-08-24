# 实验E5: 沙箱内请求脚本(触发 webhook.site 匹配转发, 稳定触发域)
import sys, urllib.request, ssl

label = sys.argv[1] if len(sys.argv) > 1 else "latest"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = f"https://webhook.site/{label}"
req = urllib.request.Request(url)
try:
    r = urllib.request.urlopen(req, context=ctx, timeout=25)
    body = r.read(1500)
    print(f"[{label}] -> {r.status}", flush=True)
    print(body[:1200], flush=True)
except urllib.error.HTTPError as e:
    body = e.read(1000)
    print(f"[{label}] -> HTTPError {e.code}", flush=True)
    print(body[:800], flush=True)
except Exception as e:
    print(f"[{label}] -> EXC {type(e).__name__}: {e}", flush=True)
