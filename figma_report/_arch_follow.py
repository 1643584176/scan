# -*- coding: utf-8 -*-
"""挖 follow / block / restrict 写操作端点"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
js_dir = r'D:\scan\figma_report\_js'
pats = [
    r'/api/followers[^"\']{0,70}',
    r'/api/following[^"\']{0,70}',
    r'followers[^"\']{0,40}follow',
    r'block[^"\']{0,40}profile',
    r'restrict[^"\']{0,60}',
    r'/api/community/profiles/[^"\']{0,80}',
]
seen = set()
for f in sorted(glob.glob(os.path.join(js_dir, '*.min.js'))):
    data = open(f, encoding='utf-8', errors='ignore').read()
    for p in pats:
        for m in re.finditer(p, data):
            ctx = data[max(0, m.start()-150):m.end()+120].replace('\n', ' ')
            key = ctx[:180]
            if key in seen:
                continue
            seen.add(key)
            print(os.path.basename(f), '::', ctx[:300])
            print()
print('TOTAL', len(seen))
