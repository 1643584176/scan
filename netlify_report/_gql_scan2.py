# -*- coding: utf-8 -*-
"""主 bundle 中 GraphQL/connect endpoint 定位"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
pats = [r'[A-Za-z0-9._\-/]*graphql[A-Za-z0-9._\-/]*',
        r'https?://[A-Za-z0-9.\-/]{5,100}',
        r'["\']/[A-Za-z0-9._\-/]{3,80}["\']']
seen = set()
for pat in pats:
    for m in re.finditer(pat, data):
        s = m.group(0)
        key = s[:120]
        if key in seen:
            continue
        seen.add(key)
        low = s.lower()
        if 'graphql' in low or 'connect' in low or 'federation' in low or 'api.netlify' in low or 'services.netlify' in low:
            print(pat[:20], '->', s[:150])
