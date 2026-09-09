# -*- coding: utf-8 -*-
"""app.js 中搜索 API token 相关片段(处理超长行)"""
import re

path = r"D:\scan\h1kit\_h1x4_app.js"
data = open(path, "r", encoding="utf-8", errors="replace").read()
print("len:", len(data))

pats = [
    r"api[_-]?token",
    r"revokeUserApiToken",
    r"updateUserApiToken",
    r"unhashed",
    r"identifier",
]
for p in pats:
    hits = [m.start() for m in re.finditer(p, data, re.I)]
    print("\n### pattern:", p, "hits:", len(hits))
    for h in hits[:8]:
        print(repr(data[max(0, h - 150):h + 250]))
