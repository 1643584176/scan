# 实验E1: forwardURL + match 组合语义
# policy: custom + allowedDomains=[httpbin.org]
# update: allow风格 httpbin.org -> [{match:{path:{exact:"/anything"}}, forwardURL:"https://httpbin.org/anything"}]
# 请求矩阵:
#   1) /anything              -> 匹配 -> 转发(预期 Vercel-Forwarded-* 头)
#   2) /other                 -> 不匹配 -> 直通 or 拒绝? (关键)
#   3) /anything/../anything  -> dot-segment 规范化后匹配? 转发用原始还是规范化路径?
#   4) /anything?x=1          -> query 不影响 path match?
#   5) POST /anything         -> method 未指定 = 任意方法?
#   6) /Anything              -> 大小写不匹配?
#   7) /anything/             -> 尾斜杠?
import urllib.request, ssl, json

def fetch(method, path):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = f"https://httpbin.org{path}"
    req = urllib.request.Request(url, method=method)
    try:
        r = urllib.request.urlopen(req, context=ctx, timeout=20)
        body = r.read(4000)
        h = dict(r.headers)
        vf = {k: v for k, v in h.items() if k.lower().startswith("vercel-")}
        return r.status, vf, body
    except Exception as e:
        return None, {}, str(e).encode()

cases = [
    ("GET", "/anything"),
    ("GET", "/other"),
    ("GET", "/anything/../anything"),
    ("GET", "/anything?x=1"),
    ("POST", "/anything"),
    ("GET", "/Anything"),
    ("GET", "/anything/"),
]
for method, p in cases:
    st, vf, body = fetch(method, p)
    print(f"== {method} {p} -> status={st} fwd_headers={list(vf.keys())}")
    for k, v in vf.items():
        print(f"   {k}: {v[:150]}")
    try:
        d = json.loads(body)
        print("   body.url:", d.get("url"))
        hh = {k: v for k, v in d.get("headers", {}).items() if k.lower().startswith(("vercel", "x-"))}
        if hh:
            print("   body.headers:", hh)
    except Exception:
        print("   body[:180]:", body[:180])
    print()
