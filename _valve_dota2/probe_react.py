# -*- coding: utf-8 -*-
"""探测 dota2 /react/ 端点:认证要求、参数行为"""
import urllib.request, ssl, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def req(method, path, data=None):
    r = urllib.request.Request(f"https://www.dota2.com{path}", headers={'User-Agent': UA}, method=method)
    if data is not None:
        r.data = data.encode()
    try:
        resp = urllib.request.urlopen(r, context=ctx, timeout=20)
        return resp.status, resp.read().decode('utf-8', 'replace')[:150]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:150]
    except Exception as e:
        return 'ERR', str(e)[:100]

# GET 端点
for ep in ["getwatchedgames", "getspoilerblock", "getlivestreams", "getfavoriteteams",
           "inference", "steam_spinner", "getbpprices?item_defs=27458"]:
    s, b = req("GET", f"/react/{ep}")
    print(f"GET  /react/{ep:<42} => {s} | {b}")

# POST 写端点
for ep, body in [("setwatchedgame", "game_id=1"), ("setspoilerblock", "block=1"),
                 ("togglefavoriteteam", "team_id=1"), ("login_mobile_auth", "{}")]:
    s, b = req("POST", f"/react/{ep}", body)
    print(f"POST /react/{ep:<42} => {s} | {b}")
    s2, b2 = req("GET", f"/react/{ep}")
    print(f"GET  /react/{ep:<42} => {s2} | {b2}")
