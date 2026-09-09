# -*- coding: utf-8 -*-
"""假设验证:user token 是否认证站内 GraphQL / 其他入口"""
import base64
import json
import urllib.request
import urllib.error

TOKEN = "xh/HVu9F69JXKIxyxX1pFdFxV+sdIUcsJxsr4KcxEzs="
OUT = []


def call(url, hdrs, body=None, method="GET"):
    r = urllib.request.Request(url, data=body, method=method)
    for k, v in hdrs.items():
        r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:500]
    except Exception as e:
        return 0, str(e)


basic_user = base64.b64encode(("base_alert:" + TOKEN).encode()).decode()
basic_nouser = base64.b64encode((":" + TOKEN).encode()).decode()

# 1) 站内 GraphQL + Basic(两种 username)+ Bearer,无 cookie
q = json.dumps({"query": "{ me { id username email has_api_token } }"}).encode()
for name, auth in [("basic-user", "Basic " + basic_user),
                   ("basic-nouser", "Basic " + basic_nouser),
                   ("bearer", "Bearer " + TOKEN)]:
    s, b = call("https://hackerone.com/graphql",
                {"Content-Type": "application/json", "Authorization": auth,
                 "Accept": "application/json"}, body=q, method="POST")
    OUT.append("===== graphql %s\nHTTP %s %s" % (name, s, b))

# 2) 站内其他 API 面
for p in ["/api/v1/me", "/api/me", "/api/v1/hackers/me"]:
    s, b = call("https://hackerone.com" + p,
                {"Authorization": "Basic " + basic_user, "Accept": "application/json"})
    OUT.append("===== hackerone.com %s\nHTTP %s %s" % (p, s, b))

# 3) api.hackerone.com username 空
s, b = call("https://api.hackerone.com/v1/hackers/me",
            {"Authorization": "Basic " + basic_nouser, "Accept": "application/json"})
OUT.append("===== api.hackerone.com nouser\nHTTP %s %s" % (s, b))

with open(r"D:\scan\h1kit\_h1x134_auth_diag5_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done")
