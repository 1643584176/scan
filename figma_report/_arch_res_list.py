# -*- coding: utf-8 -*-
"""找 community 资源列表/搜索/详情 API 路径模式"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
pats = [
    re.compile(r'["\'`]((?:/api/)?(?:community|resources|resource)[^"\'`]{0,70}(?:search|explore|list|feed|browse|discover)[^"\'`]{0,40})["\'`]', re.I),
    re.compile(r'["\'`](/api/[a-z_]+(?:search|feed|browse)[^"\'`]{0,60})["\'`]', re.I),
    re.compile(r'["\'`]((?:https?:)?//[^"\'`]*?/community[^"\'`]{0,70})["\'`]'),
    re.compile(r'resourceType[^,;]{0,30}(?:make|plugin|file|widget|template)'),
]
seen = set()
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    try:
        data = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for p in pats:
        for m in p.finditer(data):
            try:
                s = m.group(1)
            except IndexError:
                s = m.group(0)
            if s not in seen and len(s) < 120:
                seen.add(s)
                print(f'{s}  @ {os.path.basename(f)}')
print('TOTAL', len(seen))
