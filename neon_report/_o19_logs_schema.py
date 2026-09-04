# -*- coding: utf-8 -*-
"""Logs tag 路径 + schema"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
schemas = d.get('components', {}).get('schemas', {})

def resolve(ref):
    return schemas.get(ref.split('/')[-1], {})

for p, ops in paths.items():
    for m, op in ops.items():
        if isinstance(op, dict) and 'Logs' in (op.get('tags') or []):
            print('=' * 70)
            print('%s %s | %s' % (m.upper(), p, op.get('summary', '')))
            for prm in op.get('parameters', []):
                sch = prm.get('schema', {})
                if '$ref' in sch:
                    sch = resolve(sch['$ref'])
                print('  param: %s %s req=%s default=%s enum=%s desc=%s' % (
                    prm.get('in'), prm.get('name'), prm.get('required', False),
                    sch.get('default'), sch.get('enum'), (prm.get('description') or '')[:100]))
            rb = op.get('requestBody', {})
            if rb:
                for ct, cdef in rb.get('content', {}).items():
                    sch = cdef.get('schema', {})
                    if '$ref' in sch:
                        sch = resolve(sch['$ref'])
                    print('  body: %s' % json.dumps(sch)[:500])
            for code, rdef in (op.get('responses') or {}).items():
                if code.startswith('2'):
                    for ct, cdef in rdef.get('content', {}).items():
                        sch = cdef.get('schema', {})
                        if '$ref' in sch:
                            sch = resolve(sch['$ref'])
                        print('  resp %s: %s' % (code, json.dumps(sch)[:300]))
