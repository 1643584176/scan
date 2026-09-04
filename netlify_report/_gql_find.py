# -*- coding: utf-8 -*-
"""找 GraphQL 端点/调用:net_app.js 中 graphql 相关上下文"""
import re, os

for fn in ['net_app.js', 'net_lib.js', 'net_helpers.js', 'net_actions.js', 'net_ui.js']:
    p = os.path.join(r'D:\scan\netlify_report\_js', fn)
    if not os.path.exists(p):
        continue
    data = open(p, encoding='utf-8', errors='ignore').read()
    hits = [m.start() for m in re.finditer(r'graphql', data, re.I)]
    if not hits:
        continue
    print('== %s (%d hits) ==' % (fn, len(hits)))
    seen = set()
    for i in hits[:10]:
        seg = data[max(0, i - 200):i + 250]
        # 只打印含 URL/query/mutation/endpoint 特征的段
        if re.search(r'https?://|"/|query|mutation|endpoint|fetch\(|axios|request\(', seg):
            key = seg[:120]
            if key in seen:
                continue
            seen.add(key)
            print('  ...%s...' % seg.replace('\n', ' '))
            print()
