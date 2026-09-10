# -*- coding: utf-8 -*-
import io, re, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

kws = ('getPaginatedVersions', 'PaginatedVersions', 'versionIds')
for fn in ['_js/figma_app-main.js'] + sorted(glob.glob('_js/*.js')):
    try:
        t = open(fn, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    hits = []
    for kw in ('getPaginatedVersions', 'PaginatedVersions'):
        for m in re.finditer(re.escape(kw), t):
            hits.append((kw, m.start()))
    if not hits:
        continue
    print(f'===== {fn} hits={len(hits)} =====')
    seen = set()
    for kw, pos in hits[:10]:
        a = max(0, pos - 450); b = min(len(t), pos + 450)
        seg = t[a:b]
        key = seg[:80]
        if key in seen: continue
        seen.add(key)
        print(f'--- @{pos} [{kw}] ---')
        print(seg)
        print()
