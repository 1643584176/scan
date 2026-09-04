# -*- coding: utf-8 -*-
"""从 v103/v104 输出中提取 proto/service 线索"""
import re, io

for fn in ['_run_v103_out.txt', '_run_v104_out.txt']:
    print('=' * 20, fn)
    try:
        txt = io.open(fn, encoding='utf-8', errors='replace').read()
    except Exception as e:
        print('skip', e)
        continue
    hits = re.findall(r'proto hits: (\d+)', txt)
    print('proto hits:', hits[:3])
    pats = re.findall(r'[A-Za-z0-9_/.]+\.proto\b', txt)
    seen = set()
    for p in pats:
        if p not in seen:
            seen.add(p)
            print(p)
    svcs = re.findall(r'[a-z][a-z0-9.]*\.v\d\.[A-Za-z0-9_.]+', txt)
    for s in sorted(set(svcs))[:30]:
        print('SVC:', s)
