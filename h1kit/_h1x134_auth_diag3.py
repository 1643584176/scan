# -*- coding: utf-8 -*-
"""重试 Basic auth(username 变体含 token 自身/数字 id)"""
import base64
import urllib.request
import urllib.error

TOKEN = "bF9gJTA7TeKMC+ADx6hrKefniB6dxtJu5JlT4L/GROE="
OUT = []


def hit(user):
    auth = base64.b64encode(("%s:%s" % (user, TOKEN)).encode()).decode()
    r = urllib.request.Request("https://api.hackerone.com/v1/hackers/me")
    r.add_header("Authorization", "Basic " + auth)
    r.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return 0, str(e)


for user in ["base_alert", "1643584176@qq.com", "4421190",
             TOKEN, "base_alert" + TOKEN[:4]]:
    s, b = hit(user)
    OUT.append("===== user=%s\nHTTP %s %s" % (user, s, b))

with open(r"D:\scan\h1kit\_h1x134_auth_diag3_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done")
