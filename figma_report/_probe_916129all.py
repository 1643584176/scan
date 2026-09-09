# -*- coding: utf-8 -*-
"""全 chunk 搜 916129 模块定义 (各种 webpack 格式)"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
for fn in sorted(os.listdir(JS)):
    if not fn.endswith('.js'):
        continue
    p = os.path.join(JS, fn)
    data = open(p, encoding='utf-8', errors='replace').read()
    for pat in [r'916129:\s*\([^)]*\)\s*=>', r'916129:\s*function', r'916129:\s*async', r'\.916129\s*=', r',916129\s*[,:]']:
        for m in re.finditer(pat, data):
            s = max(0, m.start() - 60)
            print(f'=== {fn} DEF@ {m.start()} [{pat[:20]}]:')
            print(f'   {data[s:m.start()+700][:800]}')
            print()
print('ALL DONE')
