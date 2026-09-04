# -*- coding: utf-8 -*-
"""Functions 相关 schema 全字段 + 全路径中 function 关键词"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
schemas = d.get('components', {}).get('schemas', {})
paths = d.get('paths', {})

for name in ['NeonFunction', 'NeonFunctionDeployment', 'NeonFunctionsListResponse',
             'CustomDomainsListResponse', 'CustomDomain', 'FunctionDeploymentCreateRequest']:
    if name in schemas:
        print('=' * 70)
        print(name)
        print(json.dumps(schemas[name], indent=1)[:2200])

print('\n=== paths containing function/custom-domain ===')
for p in paths:
    pl = p.lower()
    if 'function' in pl or 'domain' in pl:
        print(' ', p)
