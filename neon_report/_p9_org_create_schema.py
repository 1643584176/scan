# -*- coding: utf-8 -*-
"""POST /organizations 完整 body schema"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
schemas = d.get('components', {}).get('schemas', {})
op = d.get('paths', {}).get('/organizations', {}).get('post', {})

def resolve(ref):
    return schemas.get(ref.split('/')[-1], {})

print('summary:', op.get('summary'))
print('headers/params:')
for prm in op.get('parameters', []):
    print('  ', prm.get('in'), prm.get('name'), prm.get('required'), prm.get('schema'))
for ct, cdef in op.get('requestBody', {}).get('content', {}).items():
    sch = cdef.get('schema', {})
    if '$ref' in sch:
        sch = resolve(sch['$ref'])
    print('\nbody[%s]:' % ct)
    print(json.dumps(sch, indent=1)[:2000])
    # 引用的子 schema
    for prop in sch.get('properties', {}).values():
        r = prop.get('$ref') or (prop.get('allOf') or [{}])[0].get('$ref')
        if r:
            sub = resolve(r)
            print('\n  sub-schema %s:' % r)
            print('  ' + json.dumps(sub, indent=1)[:1500])
