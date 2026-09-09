# -*- coding: utf-8 -*-
"""搜文件分享/权限列表端点 URL (share 弹窗数据源)"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + [f for f in os.listdir(JS) if f.endswith('.min.js')]
pats = [r'url`[^`]*(?:share|access|collaborator|invite)[^`]*file[^`]*`', r'url`[^`]*file[^`]*(?:share|access|invite)[^`]*`']
seen = set()
for fn in files:
    try:
        d = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for p in pats:
        for m in re.finditer(p, d):
            u = m.group(0)[:150]
            if u in seen:
                continue
            seen.add(u)
            s = max(0, m.start() - 120)
            print(f'{fn}: {d[s:m.end()+100][:300]}')
            print()
print('ALL DONE')
