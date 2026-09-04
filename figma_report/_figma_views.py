# -*- coding: utf-8 -*-
"""从已下载 JS 提取 livegraph viewName 全集"""
import os, re

D = 'D:/scan/figma_report/_js/'
views = set()
pat = re.compile(r'["\']([A-Z][A-Za-z0-9_]*View)["\']')
for fn in os.listdir(D):
    if not fn.endswith('.js'):
        continue
    try:
        c = open(os.path.join(D, fn), 'r', encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in pat.finditer(c):
        views.add(m.group(1))
for v in sorted(views):
    print(v)
print('total:', len(views))
