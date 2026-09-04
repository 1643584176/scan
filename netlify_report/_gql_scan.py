# -*- coding: utf-8 -*-
"""扫描 bundle 中 GraphQL endpoint"""
import re

for fn in [r'D:\scan\netlify_report\_js\net_graphql.js', r'D:\scan\netlify_report\_js\net_graphiql.js']:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    print('=' * 70)
    print(fn, len(data))
    for pat in [r'https?://[A-Za-z0-9.\-/]*graphql[A-Za-z0-9.\-/]*',
                r'url["\']?\s*[:=]\s*["\'][^"\']{5,120}["\']',
                r'endpoint["\']?\s*[:=]\s*["\'][^"\']{5,120}["\']',
                r'fetch\(["\'][^"\']{5,160}["\']']:
        hits = re.findall(pat, data, re.I)
        for h in hits[:20]:
            print(' ', h[:170])
