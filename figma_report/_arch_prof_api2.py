# -*- coding: utf-8 -*-
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
js_dir = r'D:\scan\figma_report\_js'
pats = [
    r'api/community[^"\']{0,60}',
    r'/api/community_profiles[^"\']{0,80}',
    r'/api/profiles[^"\']{0,80}',
    r'profilesUrl[^,;]{0,80}',
    r'/api/community_comments[^"\']{0,80}',
    r'community_comments[^"\']{0,60}',
]
seen = set()
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    data = open(f, encoding='utf-8', errors='ignore').read()
    for p in pats:
        for m in re.finditer(p, data):
            ctx = data[max(0, m.start()-80):m.end()+40].replace('\n', ' ')
            key = ctx[:200]
            if key in seen:
                continue
            seen.add(key)
            print(os.path.basename(f), '::', ctx[:280])
print('TOTAL', len(seen))
