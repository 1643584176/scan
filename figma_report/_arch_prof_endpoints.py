# -*- coding: utf-8 -*-
"""从 bundle 提取 profile/community 服务 API 端点字面量"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
pat = re.compile(r'["\'`](/api/(?:profile|community|resource|collection|published_package|follower|follow)[^"\'`]{0,90})["\'`]')
pat2 = re.compile(r'["\'`]((?:https?:)?//[^"\'`]*?/api/(?:profile|community|resource|collection)[^"\'`]{0,60})["\'`]')

hits = {}
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    try:
        data = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    if 'profile' not in data:
        continue
    for m in pat.finditer(data):
        hits.setdefault(m.group(1), set()).add(os.path.basename(f))
    for m in pat2.finditer(data):
        hits.setdefault(m.group(1), set()).add(os.path.basename(f))

for ep in sorted(hits):
    print(f'{ep}  <- {len(hits[ep])} files')
print('TOTAL', len(hits))
