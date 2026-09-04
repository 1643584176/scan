# -*- coding: utf-8 -*-
import os, re, json
base = r'D:\scan\netlify_report\_openapi'
for root, dirs, files in os.walk(base):
    for fn in files:
        if not (fn.endswith('.json') or fn.endswith('.yaml') or fn.endswith('.yml')):
            continue
        p = os.path.join(root, fn)
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if 'deploys' not in t:
            continue
        # 打印 deploy 相关 path 与方法
        for m in re.finditer(r'"/?(api/v1/)?deploys[^"]*"|/deploys/\{deploy_id\}', t):
            s = max(0, m.start() - 100)
            print(p, '|', t[s:m.end() + 120].replace('\n', ' ')[:250])
