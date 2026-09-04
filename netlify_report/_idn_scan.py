# -*- coding: utf-8 -*-
"""bundle 中 identity 相关 API 路径"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
seen = set()
for m in re.finditer(r'["\'`](/[A-Za-z0-9._\-/{}$]{3,90})["\'`]', data):
    p = m.group(1)
    if re.search(r'identity|jwt|sso|password|invite|user', p, re.I):
        key = p
        if key in seen:
            continue
        seen.add(key)
        print(p)
