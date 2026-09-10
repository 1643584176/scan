# -*- coding: utf-8 -*-
"""app.js 考古:api.hackerone.com / token 消费点 / settings 路由"""
import re

data = open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace").read()

pats = [
    r"api\.hackerone\.com",
    r"identifier.{0,80}token",
    r"token.{0,40}identifier",
    r"Authorization.{0,120}",
    r"api_token(s)?/[a-z_]*",
]
for p in pats:
    hits = [m.start() for m in re.finditer(p, data, re.I)]
    print("\n### pattern:", p, "hits:", len(hits))
    for h in hits[:10]:
        print(repr(data[max(0, h - 200):h + 300]))
