# -*- coding: utf-8 -*-
"""API 认证变体:Bearer/Basic x v1/v2 x id/username"""
import base64
import urllib.request
import urllib.error

TOKEN = "bF9gJTA7TeKMC+ADx6hrKefniB6dxtJu5JlT4L/GROE="
OUT = []


def hit(base, path, hdrs):
    r = urllib.request.Request(base + path)
    for k, v in hdrs.items():
        r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, body[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return 0, str(e)


for base in ["https://api.hackerone.com/v1", "https://api.hackerone.com/v2"]:
    for kind, user in [("basic-user", "base_alert"), ("basic-email", "1643584176@qq.com")]:
        auth = base64.b64encode(("%s:%s" % (user, TOKEN)).encode()).decode()
        s, b = hit(base, "/hackers/me" if "v1" in base else "/me",
                    {"Authorization": "Basic " + auth, "Accept": "application/json"})
        OUT.append("===== %s %s %s\nHTTP %s %s" % (base, kind, "hackers/me", s, b))
    s, b = hit(base, "/me", {"Authorization": "Bearer " + TOKEN, "Accept": "application/json"})
    OUT.append("===== %s bearer /me\nHTTP %s %s" % (base, s, b))
    s, b = hit(base, "/reports/3732660", {"Authorization": "Bearer " + TOKEN, "Accept": "application/json"})
    OUT.append("===== %s bearer /reports/3732660\nHTTP %s %s" % (base, s, b))

with open(r"D:\scan\h1kit\_h1x134_auth_diag2_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done")
