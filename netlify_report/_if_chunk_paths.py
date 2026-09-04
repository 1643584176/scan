# -*- coding: utf-8 -*-
"""扫全部 js chunk:api 路径全集(排除 net_app.js 已知面),找隐藏端点"""
import re, os, collections

d = r'D:\scan\netlify_report\_js'
known = set(re.findall(r'/api/v1/[A-Za-z0-9_{}./\-]+', open(os.path.join(d, 'net_app.js'), encoding='utf-8', errors='ignore').read()))

for fn in os.listdir(d):
    if not fn.endswith('.js') or fn == 'net_app.js':
        continue
    data = open(os.path.join(d, fn), encoding='utf-8', errors='ignore').read()
    paths = set(re.findall(r'["`](/api/v1/[A-Za-z0-9_{}./\-]+)["`]', data))
    paths |= set(re.findall(r'concat\([^)]*,\s*["`](/api/v1/[A-Za-z0-9_{}./\-]+)', data))
    new = paths - known
    if new:
        print('==', fn, '==')
        for p in sorted(new):
            print('   ', p)
print()
print('net_app.js 已知 /api/v1 路径数:', len(known))
for p in sorted(known):
    if re.search(r'env|secret|key|token|database|hook|function', p):
        print('   ', p)
