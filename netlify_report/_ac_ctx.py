# -*- coding: utf-8 -*-
"""access-control/bb-api 调用上下文 + 全部 /access-control 路径"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

paths = sorted(set(re.findall(r'/access-control/[A-Za-z0-9_\-{}/.]+', data)))
print('== access-control 路径 ==')
for p in paths[:40]:
    print(' ', p)

# bb-api 使用上下文
hits = [m.start() for m in re.finditer(r'bb-api', data)]
print('\n== bb-api 上下文(%d) ==' % len(hits))
seen = set()
for i in hits[:8]:
    seg = data[max(0, i - 600):i + 600]
    key = seg[:100]
    if key in seen:
        continue
    seen.add(key)
    print('...%s...' % seg.replace('\n', ' '))
    print('---')
