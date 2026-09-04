# -*- coding: utf-8 -*-
"""api_keys 端点 schema:创建参数/角色/权限字段"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
schemas = d.get('components', {}).get('schemas', {})

def resolve(ref):
    return schemas.get(ref.split('/')[-1], {})

for p in sorted(paths):
    if 'api_key' in p.lower() and p.count('/') <= 3:
        for m, op in paths[p].items():
            if not isinstance(op, dict):
                continue
            print('=' * 72)
            print('%s %s | %s' % (m.upper(), p, op.get('summary', '')))
            for prm in op.get('parameters', []):
                sch = prm.get('schema', {})
                if '$ref' in sch:
                    sch = resolve(sch['$ref'])
                print('  param %s %s req=%s %s' % (prm.get('in'), prm.get('name'),
                                                   prm.get('required', False), json.dumps(sch)[:250]))
            rb = op.get('requestBody', {})
            for ct, cdef in rb.get('content', {}).items():
                sch = cdef.get('schema', {})
                if '$ref' in sch:
                    sch = resolve(sch['$ref'])
                print('  body[%s]: %s' % (ct, json.dumps(sch, indent=1)[:1800]))
