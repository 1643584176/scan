# -*- coding: utf-8 -*-
"""离线:transfer/invitations/members 端点参数与 body schema 细节"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comp = spec['components']['schemas']

paths = spec['paths']
TARGETS = [
    ('/organizations/{org_id}/invitations', 'post'),
    ('/organizations/{org_id}/members/{member_id}', 'patch'),
    ('/projects/{project_id}/transfer_requests', 'post'),
    ('/projects/{project_id}/transfer_requests/{request_id}', 'put'),
    ('/projects/{project_id}/members', 'get'),
    ('/projects/{project_id}/members/{member_id}/role', 'put'),
    ('/organizations/{source_org_id}/projects/transfer', 'post'),
    ('/projects/auth/transfer_ownership', 'post'),
    ('/users/me/projects/transfer', 'post'),
]
for p, m in TARGETS:
    op = spec['paths'].get(p, {}).get(m)
    if not op:
        print('== %s %s NOT FOUND' % (m.upper(), p))
        continue
    print('\n== %s %s | %s' % (m.upper(), p, op.get('summary', '')))
    for pa in op.get('parameters', []):
        sch = pa.get('schema', {})
        print('  param %s (%s) %s default=%s' % (pa.get('name'), pa.get('in'), sch.get('type'), sch.get('default', '')))
    rb = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
    ref = rb.get('$ref', '')
    if ref:
        name = ref.split('/')[-1]
        sch = comp.get(name, {})
        print('  body schema: %s' % name)
        for k, v in sch.get('properties', {}).items():
            d = v.get('description', '')
            rr = v.get('$ref', '')
            print('    %s: type=%s ref=%s req=%s | %s' % (k, v.get('type'), rr, k in sch.get('required', []), d[:150]))
            if v.get('enum'):
                print('       enum:', v['enum'])
        if sch.get('description'):
            print('  desc:', sch['description'][:200])
    # 响应 schema
    rc = op.get('responses', {}).get('201') or op.get('responses', {}).get('200')
    if rc:
        rref = rc.get('content', {}).get('application/json', {}).get('schema', {})
        print('  resp ref:', rref.get('$ref', ''))
