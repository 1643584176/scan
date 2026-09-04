# -*- coding: utf-8 -*-
"""member schema + invites path + member 完整对象"""
import yaml

spec = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
paths = spec['paths']

print('=== POST /{account_slug}/members 定义 ===')
op = paths['/{account_slug}/members'].get('post', {})
rb = op.get('requestBody', {})
for ct, cdef in rb.get('content', {}).items():
    sch = cdef.get('schema', {})
    print('body:', ct, json.dumps(sch, indent=1)[:800])
    ref = sch.get('$ref')
    if ref:
        name = ref.split('/')[-1]
        d = spec['components']['schemas'][name]
        print('schema %s props:' % name, list(d.get('properties', {}).keys()))
        for pn, pv in d.get('properties', {}).items():
            print('   ', pn, ':', pv.get('type'), pv.get('enum', ''), pv.get('description', '')[:60])

print()
print('=== PUT /{account_slug}/members/{member_id} 定义 ===')
op = paths['/{account_slug}/members/{member_id}'].get('put', {})
for prm in op.get('parameters', []):
    print('param:', prm.get('name'), prm.get('in'), prm.get('required'))
rb = op.get('requestBody', {})
for ct, cdef in rb.get('content', {}).items():
    print('body:', ct, json.dumps(cdef.get('schema', {}), indent=1)[:500])

print()
print('=== 含 invite 的 path ===')
for p in sorted(paths.keys()):
    if 'invite' in p.lower() or 'accept' in p.lower():
        print(' ', p, '->', [m for m in paths[p] if m in ('get','post','put','patch','delete')])

import json as j
print()
print('=== member schema(components) ===')
for n in ['Member', 'Membership', 'Invite']:
    if n in spec.get('components', {}).get('schemas', {}):
        d = spec['components']['schemas'][n]
        print(n, ':', list(d.get('properties', {}).keys()))
