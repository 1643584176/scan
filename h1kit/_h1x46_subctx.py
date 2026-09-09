# -*- coding: utf-8 -*-
"""h1x46: /subscription.json 调用上下文挖掘"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
idxs = [m.start() for m in re.finditer(r'/subscription\.json', t)]
print('occurrences:', len(idxs))
for i in idxs[:5]:
    seg = t[max(0, i-2500):i+800]
    print('=' * 80)
    print('@', i)
    print(seg[:3300])
