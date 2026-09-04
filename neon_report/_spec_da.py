# -*- coding: utf-8 -*-
"""离线查 spec:data-api 端点 + 相关 schema 字段"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))

print('==== data-api paths ====')
for p in sorted(spec['paths']):
    if 'data-api' in p.lower():
        print('PATH', p)
        for m in spec['paths'][p]:
            if m not in ('get', 'post', 'patch', 'put', 'delete'):
                continue
            op = spec['paths'][p][m]
            rb = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
            ref = rb.get('$ref', '')
            resp = op.get('responses', {}).get('200', {}).get('content', {}).get('application/json', {}).get('schema', {})
            print('   ', m.upper(), op.get('operationId'), '| req:', ref, '| resp:', resp.get('$ref', list(resp.get('properties', {}).keys())))

print('\n==== components: DataAPI/BranchDataAPI/JWT/Auth 相关 ====')
for name, sch in spec.get('components', {}).get('schemas', {}).items():
    n = name.lower()
    if any(k in n for k in ['dataapi', 'jwt', 'authprovider', 'neonauth', 'connection']):
        props = list(sch.get('properties', {}).keys()) if isinstance(sch, dict) else []
        print('-', name, ':', props)
