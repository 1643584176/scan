# -*- coding: utf-8 -*-
"""提取新端点调用上下文: HTTP 方法/参数/周边逻辑"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'
targets = [
    'community_publishers/accept', 'community_publishers/remove',
    'followers/', 'following/', 'resource_saves', 'resources/',
    'community/seller', 'related_content',
]
files = {}
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    try:
        data = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for t in targets:
        if t in data:
            files.setdefault(t, []).append(os.path.basename(f))

for t, fl in files.items():
    print(f'### {t}: {len(fl)} files -> {fl[:6]}')

# 对每个目标,在第一个文件里挖上下文 (方法+URL+body)
seen = set()
for t in targets:
    for f in files.get(t, [])[:2]:
        fp = os.path.join(js_dir, f)
        data = open(fp, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(re.escape(t[:20]), data):
            s = max(0, m.start() - 400)
            ctx = data[s:m.end() + 300]
            key = t + '::' + ctx[:60]
            if key in seen:
                continue
            seen.add(key)
            print('\n===== CONTEXT', t, '@', f, 'pos', m.start(), '=====')
            print(ctx[:700].replace('\n', ' '))
            break
print('\nALL DONE')
