# -*- coding: utf-8 -*-
"""深挖 935/vendor-3871c33a/auth-61211038 中的 chunk 映射与 figma_app 加载逻辑"""
import re, os

D = 'D:/scan/figma_report/_js/'
files = ['935-431f89677a39072c.min.js',
         'vendor-3871c33a541abc9e.min.js',
         'auth-61211038b210d6ec.min.js',
         'cssbuilder-11ed71357628a2b5.min.js']

for f in files:
    p = os.path.join(D, f)
    if not os.path.exists(p):
        print(f, 'MISSING'); continue
    d = open(p, 'r', encoding='utf-8', errors='ignore').read()
    print('###', f, 'len', len(d))

    # 1. webpack 运行时 chunk 映射:形如 {935:"abc...", 123:"def..."} 或 .min.js 引用
    for m in re.finditer(r'\{[0-9]{1,5}:"[0-9a-f]{8,40}"[^{}]{0,3000}\}', d):
        g = m.group(0)
        if g.count('":"') > 3:
            print('  chunkmap(%d):' % g.count('":"'), g[:500])
            break

    # 2. assets/ 路径引用
    for m in list(re.finditer(r'assets/[a-zA-Z0-9_~.-]+', d))[:10]:
        print('  asset:', m.group(0)[:120])

    # 3. figma_app 上下文
    for m in list(re.finditer(r'.{80}figma_app.{80}', d))[:8]:
        print('  figma_app ctx:', m.group(0).replace('\n', ' ')[:180])
    print()
