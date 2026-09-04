# -*- coding: utf-8 -*-
"""查 spec 全局参数 + createProject 的 org_id 传递方式"""
import json
spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
print('== global parameters:')
for p in spec.get('parameters', {}).values():
    print(' ', json.dumps(p)[:200])
print('== security schemes:')
print(json.dumps(spec.get('components', {}).get('securitySchemes', {}), indent=1)[:800])
print('== createProject op 完整:')
op = spec['paths']['/projects']['post']
print('params:', json.dumps(op.get('parameters', []), indent=1)[:500])
# listProjects 的 org_id 参数形态(作为参考)
lp = spec['paths']['/projects']['get']
for prm in lp.get('parameters', []):
    if 'org' in json.dumps(prm).lower():
        print('listProjects org param:', json.dumps(prm)[:300])
