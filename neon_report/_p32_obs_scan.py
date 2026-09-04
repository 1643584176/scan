# -*- coding: utf-8 -*-
"""1. 全 _js 目录搜 listObservabilityConfigurations / observability 端点定义
2. 黑盒: GET /ajax-api/2.0/postgres/projects/{pid}/observability-settings (A 项目 vs 不存在)
3. GraphQL 候选端点探测(richUser 查询)"
"""
import re, os, sys, json, http.client, ssl, html, time

# 1. 全目录搜
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_js')
hits = []
for fn in os.listdir(base):
    if not fn.endswith('.js'):
        continue
    p = os.path.join(base, fn)
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if 'listObservabilityConfigurations' in s or 'observability-settings' in s or 'observability/config' in s or 'ajax-api' in s:
        hits.append((fn, len(s)))
        for kw in ['listObservabilityConfigurations', 'observability-settings']:
            i = s.find(kw)
            if i >= 0:
                print('--- %s (size %d) ---' % (fn, len(s)), flush=True)
                print(s[max(0, i - 800):i + 400].replace('\n', ' ')[:1400], flush=True)
                break
print('hit files:', hits, flush=True)
