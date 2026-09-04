# -*- coding: utf-8 -*-
"""离线:users/me 方法 + projects 列表端点 + 账户字段可写性"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comp = spec['components']['schemas']

for p in ['/users/me', '/users/me/projects', '/projects', '/users/me/organizations']:
    ops = spec['paths'].get(p, {})
    print('== %s: methods %s' % (p, sorted(ops.keys())))
    for m, op in ops.items():
        if m not in ('get', 'post', 'patch', 'put', 'delete'):
            continue
        print('  %s %s | %s' % (m.upper(), op.get('operationId', ''), op.get('summary', '')))
        rb = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
        ref = rb.get('$ref', '')
        if ref:
            name = ref.split('/')[-1]
            sch = comp.get(name, {})
            print('    body %s' % name)
            for k, v in sch.get('properties', {}).items():
                print('      %s: type=%s req=%s enum=%s | %s' % (k, v.get('type'), k in sch.get('required', []), v.get('enum'), v.get('description', '')[:100]))

# UpdateCurrentUser 相关 schema
for nm in ['UpdateCurrentUserRequest', 'UpdateUserRequest', 'UserRequest', 'CurrentUserInfo']:
    sch = comp.get(nm)
    if sch:
        print('\n== schema', nm)
        for k, v in sch.get('properties', {}).items():
            print('   %s: type=%s | %s' % (k, v.get('type'), v.get('description', '')[:100]))
