# -*- coding: utf-8 -*-
"""新 token 测试:username 变体"""
import base64
import urllib.request
import urllib.error

TOKEN = "xh/HVu9F69JXKIxyxX1pFdFxV+sdIUcsJxsr4KcxEzs="
OUT = []


def hit(user, base="https://api.hackerone.com/v1"):
    auth = base64.b64encode(("%s:%s" % (user, TOKEN)).encode()).decode()
    r = urllib.request.Request(base + "/hackers/me")
    r.add_header("Authorization", "Basic " + auth)
    r.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return 0, str(e)


for user in ["base_alert", "1643584176@qq.com", "4421190", TOKEN]:
    s, b = hit(user)
    OUT.append("===== user=%s\nHTTP %s %s" % (user, s, b))

with open(r"D:\scan\h1kit\_h1x134_auth_diag4_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done")
