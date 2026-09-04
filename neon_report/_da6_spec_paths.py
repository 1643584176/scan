# -*- coding: utf-8 -*-
"""从 OpenAPI spec 提取 auth / data-api / jwks 相关端点(只读)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec.get('paths', {})
print('total paths:', len(paths))
for p in sorted(paths):
    pl = p.lower()
    if any(k in pl for k in ('auth', 'data-api', 'jwks', 'database')):
        methods = ','.join(m.upper() for m in paths[p] if m in ('get', 'post', 'patch', 'put', 'delete'))
        # 取 operationId
        ops = []
        for m in ('get', 'post', 'patch', 'put', 'delete'):
            if m in paths[p]:
                ops.append('%s:%s' % (m.upper(), paths[p][m].get('operationId', '?')))
        print(p, '->', ' '.join(ops))
