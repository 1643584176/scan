# -*- coding: utf-8 -*-
"""抽取经验库中 versions/游标/keyset 的所有上下文段落(±6行)"""
import os, io, re

DIR = r'D:/scan/经验/全局经验/SQL注入经验库'
for fn in ['01-SQL入参矩阵.md', '03-判读库.md', '05-实战案例.md', '06-送达与过障.md']:
    txt = io.open(os.path.join(DIR, fn), encoding='utf-8', errors='ignore').read()
    lines = txt.split('\n')
    hits = set()
    for i, ln in enumerate(lines):
        if re.search(r'versions|游标|keyset|µs', ln):
            for j in range(max(0, i - 4), min(len(lines), i + 5)):
                hits.add(j)
    if not hits:
        continue
    print('#' * 25, fn)
    prev = -2
    for j in sorted(hits):
        if j != prev + 1:
            print('   ...')
        print('%4d| %s' % (j + 1, lines[j][:160]))
        prev = j
    print()
