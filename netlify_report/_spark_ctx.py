# -*- coding: utf-8 -*-
"""net_app.js 中 spark-proxy 全部调用上下文"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

hits = [m.start() for m in re.finditer(r'spark-proxy', data)]
print('hits:', len(hits))
seen = set()
for i in hits:
    seg = data[max(0, i - 1500):i + 1500]
    key = seg[:80]
    if key in seen:
        continue
    seen.add(key)
    print('=' * 30)
    print(seg.replace('\n', ' '))
    print()
