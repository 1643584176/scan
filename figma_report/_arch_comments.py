# -*- coding: utf-8 -*-
"""找 community_comments 的完整调用 (GET/DELETE/回复)"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    data = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'community_comments', data):
        s = max(0, m.start() - 260)
        ctx = data[s:m.end() + 300]
        print(f'### {os.path.basename(f)} pos {m.start()} ###')
        print(ctx.replace('\n', ' ')[:520])
        print()
