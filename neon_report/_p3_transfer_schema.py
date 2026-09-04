# -*- coding: utf-8 -*-
"""transfer_requests 端点完整定义 + 相关 schema"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
schemas = d.get('components', {}).get('schemas', {})

def resolve(ref):
    return schemas.get(ref.split('/')[-1], {})

for p, ops in paths.items():
    if 'transfer' not in p.lower():
        continue
    for m, op in ops.items():
        if not isinstance(op, dict):
            continue
        print('=' * 72)
        print('%s %s | %s' % (m.upper(), p, op.get('summary', '')))
        print(' desc:', (op.get('description') or '')[:300])
        for prm in op.get('parameters', []):
            sch = prm.get('schema', {})
            if '$ref' in sch:
                sch = resolve(sch['$ref'])
            print('  param %s %s req=%s %s' % (prm.get('in'), prm.get('name'),
                                               prm.get('required', False), json.dumps(sch)[:200]))
        rb = op.get('requestBody', {})
        for ct, cdef in rb.get('content', {}).items():
            sch = cdef.get('schema', {})
            if '$ref' in sch:
                sch = resolve(sch['$ref'])
            print('  body[%s]: %s' % (ct, json.dumps(sch, indent=0)[:900]))
        for code, resp in (op.get('responses') or {}).items():
            if code not in ('200', '201', '202'):
                continue
            for ct, cdef in resp.get('content', {}).items():
                sch = cdef.get('schema', {})
                if '$ref' in sch:
                    sch = resolve(sch['$ref'])
                print('  resp %s[%s]: %s' % (code, ct, json.dumps(sch, indent=0)[:900]))

# 相关 schema 全字段
for name in ['ProjectTransferRequest', 'ProjectTransferRequestCreateRequest',
             'ProjectTransferRequestCreateResponse', 'ProjectTransferRequestAcceptRequest']:
    if name in schemas:
        print('=' * 72)
        print('SCHEMA', name)
        print(json.dumps(schemas[name], indent=1)[:2500])
