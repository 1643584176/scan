# -*- coding: utf-8 -*-
"""全库找 Community*Query 定义: 搜 'Community' 与 'PaginatedQuery/PagedQuery/fetch:' 同现"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    data = open(f, encoding='utf-8', errors='ignore').read()
    if 'Community' not in data:
        continue
    # PagedQuery({label:"CommunityXxxQuery", fetch:...
    for m in re.finditer(r'(?:PagedQuery|PaginatedQuery|Query)\(\{label:"(Community[^"]{0,60})"', data):
        print(f'### label={m.group(1)} @ {os.path.basename(f)} pos {m.start()}')
        ctx = data[m.start():m.start() + 700]
        print(ctx[:650].replace('\n', ' '))
        print()
