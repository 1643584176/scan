# -*- coding: utf-8 -*-
"""提取 DB API 端点调用上下文(方法/参数)"""
import re

d = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

pats = [
    r'/database/rotate_credentials',
    r'/database/branches',
    r'/database/branch/',
    r'/database/snapshots',
    r'/database/snapshot/',
    r'/database/settings',
    r'/database/compute/settings',
]
for p in pats:
    for m in re.finditer(re.escape(p), d):
        i = m.start()
        print(f'==== {p} @ {i} ====')
        print(d[max(0, i - 400):i + 200].replace('\n', ' ')[:650])
        print()
