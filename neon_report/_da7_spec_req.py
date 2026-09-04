# -*- coding: utf-8 -*-
"""提取 spec 中 createProject / createNeonAuth / createProjectBranchDataAPI 请求 schema(只读)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec.get('paths', {})

targets = [
    ('post', '/projects'),
    ('post', '/projects/{project_id}/branches/{branch_id}/auth'),
    ('post', '/projects/{project_id}/branches/{branch_id}/data-api/{database_name}'),
    ('post', '/projects/{project_id}/branches/{branch_id}/databases'),
    ('post', '/projects/auth/create'),
    ('post', '/projects/{project_id}/jwks'),
]
for method, p in targets:
    if p not in paths or method not in paths[p]:
        print('NOT FOUND', method, p)
        continue
    op = paths[p][method]
    print('\n==== %s %s | op=%s' % (method, p, op.get('operationId')))
    rb = op.get('requestBody', {})
    sch = rb.get('content', {}).get('application/json', {}).get('schema', {})
    print('req schema:', json.dumps(sch, ensure_ascii=False)[:800])
