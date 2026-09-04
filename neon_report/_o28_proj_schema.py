# -*- coding: utf-8 -*-
"""查 POST /projects 定义"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
schemas = d.get('components', {}).get('schemas', {})
op = paths.get('/projects', {}).get('post', {})
print('summary:', op.get('summary'))
rb = op.get('requestBody', {})
for ct, cdef in rb.get('content', {}).items():
    sch = cdef.get('schema', {})
    if '$ref' in sch:
        sch = schemas.get(sch['$ref'].split('/')[-1], {})
    print(ct)
    print(json.dumps(sch, indent=1)[:1500])
