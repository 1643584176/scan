# -*- coding: utf-8 -*-
"""feed 发帖基线: B 在自己 org 发帖, 验证接口可用性 + 拿 publicUuid
同时测 updatePost / get 接口形态 (400 反推契约)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
B_TEAM = "1667396394890946753"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, method, path, body=None, query=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:500]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:500]}")
        return e.code, raw


print("===== 1. POST 发帖 (空契约反推) =====")
call("post empty", "POST", "/api/feed_posts/", {})
call("post minimal", "POST", "/api/feed_posts/", {"orgId": B_TEAM, "title": "probe", "descriptionMeta": [], "content": []})
call("post guess2", "POST", "/api/feed_posts/",
     {"org_id": B_TEAM, "title": "probe", "description_meta": [], "content": []})

print("\n===== 2. GET 读自己 feed (REST 形态猜测) =====")
call("get feed_posts", "GET", "/api/feed_posts/", query={"org_id": B_TEAM})
call("get feed_posts user", "GET", "/api/feed_posts/", query={"user_id": "1667396392129259941", "org_id": B_TEAM})

print("\n===== 3. PUT 更新 (形态猜测) =====")
call("put feed_posts", "PUT", "/api/feed_posts/", {"orgId": B_TEAM, "title": "x"})
