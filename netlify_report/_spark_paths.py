# -*- coding: utf-8 -*-
"""spark-proxy 全部 API 路径 + prompt-templates 写操作调用"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. spark-proxy 路径全集
paths = sorted(set(re.findall(r'/spark-proxy/[A-Za-z0-9_\-{}/.]+', data)))
print('== spark-proxy 路径 ==')
for p in paths:
    print(' ', p)

# 2. prompt-templates 写操作上下文
idx = [m.start() for m in re.finditer(r'prompt-templates', data)]
print('\n== prompt-templates 上下文(%d) ==' % len(idx))
seen = set()
for i in idx[:12]:
    seg = data[max(0, i - 300):i + 600]
    key = seg[300:420]
    if key in seen:
        continue
    seen.add(key)
    print('...%s...' % seg.replace('\n', ' '))
    print()
