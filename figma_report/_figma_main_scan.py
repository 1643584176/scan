# -*- coding: utf-8 -*-
"""主 bundle 深挖:viewName / pr-pt-ph 算法 / realtime_token / 端点全集"""
import os, re

D = 'D:/scan/figma_report/_js/'
TARGETS = ['935-431f89677a39072c.min.js', 'auth-61211038b210d6ec.min.js',
           'vendor-3871c33a541abc9e.min.js', 'vendor-core-ff6ab2ad5ffa3e30.min.js']

# 1. livegraph view 名(订阅视图)
print('===== livegraph view 名 =====')
views = set()
pat = re.compile(r'["\']([A-Z][A-Za-z0-9]{3,40}View)["\']')
for fn in TARGETS:
    c = open(os.path.join(D, fn), 'r', encoding='utf-8', errors='ignore').read()
    for m in pat.finditer(c):
        views.add(m.group(1))
for v in sorted(views):
    print(' ', v)
print('total:', len(views))

# 2. livegraph 连接 URL 构造 + pr/pt/ph
print('\n===== livegraph URL 构造上下文 =====')
for fn in TARGETS:
    c = open(os.path.join(D, fn), 'r', encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'livegraph', c):
        s = max(0, m.start() - 200)
        e = min(len(c), m.end() + 300)
        ctx = c[s:e]
        if 'pr=' in ctx or 'pt=' in ctx or 'ph=' in ctx or 'api/livegraph' in ctx:
            print('--- [%s]' % fn)
            print(ctx[:500].replace('\n', ' '))
            print()
            break

# 3. realtime_token 用法
print('\n===== realtime_token 上下文 =====')
for fn in TARGETS:
    c = open(os.path.join(D, fn), 'r', encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'realtime_token', c):
        s = max(0, m.start() - 250)
        e = min(len(c), m.end() + 250)
        print('--- [%s]' % fn)
        print(c[s:e].replace('\n', ' ')[:600])
        print()
        break

# 4. /api/ 端点全集
print('\n===== /api/ 端点 =====')
eps = set()
pat2 = re.compile(r'["\'`](/api/[a-zA-Z0-9_\-/{}\.]+)["\'`]')
for fn in TARGETS:
    c = open(os.path.join(D, fn), 'r', encoding='utf-8', errors='ignore').read()
    for m in pat2.finditer(c):
        eps.add(m.group(1))
for e in sorted(eps):
    print(' ', e[:110])
print('total:', len(eps))
