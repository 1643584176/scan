# -*- coding: utf-8 -*-
"""916129 模块懒 chunk 考古: 定位模块定义 + savepoint/version 保存端点的 URL 形态"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
targets = ['940032c6-b1c2c739c723c9e9.min.js', '1674-a28b39d42736af05.min.js',
           '5613-065a64a7ed9a322e.min.js', '9300-41a18cb0f8ba922b.min.js']

for fn in targets:
    p = os.path.join(JS, fn)
    if not os.path.exists(p):
        print(f'--- {fn} MISSING')
        continue
    data = open(p, encoding='utf-8', errors='replace').read()
    print(f'=== {fn} len={len(data)}')
    # 916129 上下文
    for m in list(re.finditer(r'916129', data))[:4]:
        s = max(0, m.start() - 80)
        e = min(len(data), m.end() + 120)
        print(f'  916129@ {m.start()}: {data[s:e][:250]}')
        print()
    # 找 savepoint / version 保存 URL
    for pat in ['savepoint', 'checkpoint', 'create_version', 'addVersion', 'saveVersion']:
        hits = list(re.finditer(pat, data))[:3]
        for h in hits:
            s = max(0, h.start() - 100)
            e = min(len(data), h.end() + 150)
            print(f'  {pat}@ {h.start()}: {data[s:e][:280]}')
            print()
print('ALL DONE')
