# -*- coding: utf-8 -*-
"""定位 CommunityResourcesPagedQuery / PaginatedQuery 定义处的 URL"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    data = open(f, encoding='utf-8', errors='ignore').read()
    for kw in ['CommunityResourcesPagedQuery', 'CommunityResourcesPaginatedQuery', 'CommunityResourcesQuery']:
        for m in re.finditer(kw, data):
            s = max(0, m.start() - 80)
            ctx = data[s:m.end() + 300]
            if 'url`' in ctx or '/api/' in ctx or 'fetch:' in ctx:
                print(f'### {kw} @ {os.path.basename(f)} pos {m.start()}')
                print(ctx[:420].replace('\n', ' '))
                print()
