# -*- coding: utf-8 -*-
"""认证格式矩阵:Rails Token scheme / x-api-key / Basic 变体"""
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
            return resp.status, resp.read().decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return 0, str(e)


basic_u = base64.b64encode(("base_alert:" + TOKEN).encode()).decode()
q = json.dumps({"query": "{ me { id username email has_api_token } }"}).encode()

auths_gql = {
    "Token token=\"..\"": 'Token token="%s"' % TOKEN,
    "Token bare": "Token " + TOKEN,
    "Basic user:tok": "Basic " + basic_u,
}
for name, auth in auths_gql.items():
    s, b = call("https://hackerone.com/graphql",
                {"Content-Type": "application/json", "Authorization": auth},
                body=q, method="POST")
    OUT.append("===== graphql %s\nHTTP %s %s" % (name, s, b))

auths_api = {
    "Token token=\"..\"": 'Token token="%s"' % TOKEN,
    "Token bare": "Token " + TOKEN,
    "x-api-key": None,
}
for name, auth in auths_api.items():
    h = {"Accept": "application/json"}
    if auth:
        h["Authorization"] = auth
    else:
        h["X-Api-Key"] = TOKEN
    s, b = call("https://api.hackerone.com/v1/hackers/me", h)
    OUT.append("===== api %s\nHTTP %s %s" % (name, s, b))

# 颠倒 Basic
for pair in ["%s:%s" % (TOKEN, "base_alert"), "%s:" % TOKEN]:
    b64 = base64.b64encode(pair.encode()).decode()
    s, b = call("https://api.hackerone.com/v1/hackers/me",
                {"Authorization": "Basic " + b64, "Accept": "application/json"})
    OUT.append("===== api swapped %s\nHTTP %s %s" % (pair[:20], s, b))

with open(r"D:\scan\h1kit\_h1x134_auth_diag6_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done")
