# -*- coding: utf-8 -*-
"""考古:静态 chunk URL 前缀模式(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 找 publicPath / asset 域名
pats = [r"https://[a-z0-9.\-]+/[^\"']*static/", r"publicPath\s*[:=]\s*[\"'][^\"']+",
        r"assetPrefix[^,;]{0,80}", r"cdn[^,;]{0,60}static", r"//[a-z0-9.\-]+\.hackerone\.com"]
seen = set()
for p in pats:
    for m in re.finditer(p, data, re.I):
        s = m.group(0)
        if s not in seen:
            seen.add(s)
            print("PAT:", s[:200])
