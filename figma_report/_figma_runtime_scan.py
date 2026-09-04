# -*- coding: utf-8 -*-
"""解压 runtime/vendor-core/935 找 chunk 映射中的 figma_app 主 bundle hash"""
import brotli, re, os

D = 'D:/scan/figma_report/_js/'
files = ['runtime~auth-29ad3e317c66e703.min.js',
         'vendor-core-ff6ab2ad5ffa3e30.min.js',
         '935-431f89677a39072c.min.js']

for f in files:
    p = os.path.join(D, f)
    if not os.path.exists(p):
        print(f, 'MISSING'); continue
    try:
        d = open(p, 'r', encoding='utf-8', errors='ignore').read()
        print(f, 'len', len(d))
    except Exception as e:
        print(f, 'ERR', e); continue
    # webpack chunk 映射形如 {935:"hash", 123:"hash"}
    for m in re.finditer(r'\{[0-9"][^{}]{0,4000}\}', d):
        g = m.group(0)
        if 'figma_app' in g or (':' in g and '"' in g):
            if re.search(r'\d{2,5}:"[0-9a-f]{8,}', g):
                print('  chunkmap:', g[:400])
    for m in re.finditer(r'figma_app[^"\'\,\;]{0,60}', d):
        print('  figma_app:', m.group(0)[:90])
    # 所有 .js.br 引用
    names = set(re.findall(r'[a-zA-Z0-9_~]+-[0-9a-f]{8,}\.min\.js\.br', d))
    if names:
        print('  js.br refs (%d):' % len(names), sorted(names)[:30])
