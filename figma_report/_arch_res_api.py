# -*- coding: utf-8 -*-
"""找 community explore/feed/search 的实际 API URL 模板 (url`...` 模式)"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
# Ay.url`...` / url`...` 模板 + 邻近关键字的组合
keys = ['explore', 'search', 'feed', 'community', 'discover']
pats = [
    re.compile(r'url`([^`]{0,120})`'),
    re.compile(r'\.url\(([^)]{0,120})\)'),
]
hits = {}
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    try:
        data = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for p in pats:
        for m in p.finditer(data):
            s = m.group(1)
            if any(k in s.lower() for k in ['community', 'resource', 'explore', 'search', 'feed', 'collection', 'save']):
                # 只保留看起来是 URL 路径的
                if s.startswith('/api/') or '/api/' in s or 'community' in s.lower():
                    hits.setdefault(s[:130], 0)
                    hits[s[:130]] += 1

for s in sorted(hits, key=hits.get, reverse=True):
    print(f'{hits[s]:4d}  {s}')
print('TOTAL', len(hits))
