# -*- coding: utf-8 -*-
"""盘点 spec 全部端点按 tag 分组 + 已测标注 -> 找未测面"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec.get('paths', {})
# tag -> [(method, path, opId)]
from collections import defaultdict
by_tag = defaultdict(list)
for p, item in paths.items():
    for m in ('get', 'post', 'patch', 'put', 'delete'):
        op = item.get(m)
        if not op:
            continue
        for t in op.get('tags', ['?']):
            by_tag[t].append((m.upper(), p, op.get('operationId', '?')))

for t in sorted(by_tag):
    eps = by_tag[t]
    print('## %-22s %2d' % (t, len(eps)))
    for m, p, opid in eps:
        print('   %-6s %-72s %s' % (m, p, opid))
