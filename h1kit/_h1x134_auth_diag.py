# -*- coding: utf-8 -*-
"""API 401 诊断:username 变体 x UA 变体"""
import base64
import urllib.request
import urllib.error

TOKEN = "bF9gJTA7TeKMC+ADx6hrKefniB6dxtJu5JlT4L/GROE="
URL = "https://api.hackerone.com/v1/hackers/me"

OUT = []
for user in ["base_alert", "1643584176@qq.com", "1643584176"]:
    for ua in [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36",
        "curl/8.0",
    ]:
        auth = base64.b64encode(("%s:%s" % (user, TOKEN)).encode()).decode()
        r = urllib.request.Request(URL)
        r.add_header("Authorization", "Basic " + auth)
        r.add_header("Accept", "application/json")
        r.add_header("User-Agent", ua)
        try:
            with urllib.request.urlopen(r, timeout=20) as resp:
                body = resp.read().decode("utf-8", "replace")
                OUT.append("===== user=%s ua=%s\nHTTP %s\n%s" % (user, ua[:30], resp.status, body[:400]))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            OUT.append("===== user=%s ua=%s\nHTTP %s\n%s" % (user, ua[:30], e.code, body[:400]))
        except Exception as e:
            OUT.append("===== user=%s ua=%s\nERR %s" % (user, ua[:30], e))

with open(r"D:\scan\h1kit\_h1x134_auth_diag_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done")
