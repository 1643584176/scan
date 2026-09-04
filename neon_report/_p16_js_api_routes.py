# -*- coding: utf-8 -*-
"""从 console app.js 提取 /api/* 路由清单(前端自有 API)"""
import re

t = open('D:/scan/neon_report/_js/app.js', encoding='utf-8', errors='ignore').read()
print('js len:', len(t))

pats = sorted(set(re.findall(r'["\'](/api/[a-zA-Z0-9_\-/{}.]+)["\']', t)))
print('total:', len(pats))
for p in pats:
    print(p)
