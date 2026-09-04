# -*- coding: utf-8 -*-
"""离线 dump neon auth + data-api 相关全部 paths 及参数"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))

for p in sorted(spec['paths']):
    pl = p.lower()
    if any(k in pl for k in ['neonauth', 'auth/', 'data-api', 'jwks']):
        for m in spec['paths'][p]:
            if m not in ('get', 'post', 'patch', 'put', 'delete'):
                continue
            op = spec['paths'][p][m]
            params = []
            for pa in op.get('parameters', []):
                params.append('%s:%s' % (pa.get('name'), pa.get('in')))
            rb = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
            print('%s %-14s %-70s q:[%s] body:%s' % (m.upper(), op.get('operationId', '')[:14], p, ','.join(params), rb.get('$ref', '')))
