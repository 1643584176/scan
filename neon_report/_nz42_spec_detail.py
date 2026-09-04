# -*- coding: utf-8 -*-
"""数据管理面关键端点 schema 详查 (离线)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec['paths']
schemas = spec['components']['schemas']

def deref(ref):
    return schemas.get(ref.split('/')[-1]) if ref else None

want = [
    ('get', '/projects/{project_id}/permissions'),
    ('post', '/projects/{project_id}/permissions'),
    ('delete', '/projects/{project_id}/permissions/{permission_id}'),
    ('post', '/projects/{project_id}/transfer_requests'),
    ('put', '/projects/{project_id}/transfer_requests/{request_id}'),
    ('post', '/organizations/{source_org_id}/projects/transfer'),
    ('post', '/users/me/projects/transfer'),
    ('get', '/organizations/{org_id}/invitations'),
    ('post', '/organizations/{org_id}/invitations'),
    ('post', '/projects/{project_id}/branches/{branch_id}/restore'),
    ('post', '/projects/{project_id}/branches/{branch_id}/finalize_restore'),
    ('post', '/projects/{project_id}/recover'),
    ('get', '/projects/{project_id}/branches/{branch_id}/compare_schema'),
    ('get', '/projects/{project_id}/branches/{branch_id}/schema'),
    ('put', '/projects/{project_id}/branches/{branch_id}/backup_schedule'),
    ('post', '/projects/{project_id}/branches/{branch_id}/snapshot'),
    ('get', '/projects/shared'),
]

def show_schema(sch, indent=0):
    if not sch:
        return
    pre = '  ' * indent
    props = sch.get('properties', {})
    reqs = sch.get('required', [])
    if reqs:
        print(pre + 'required: %s' % reqs)
    for k, v in props.items():
        if '$ref' in v:
            t = 'ref:' + v['$ref'].split('/')[-1]
        else:
            t = v.get('type', v.get('enum', v.get('example', '')))
        d = str(v.get('description', ''))[:100].replace('\n', ' ')
        print('%s- %-30s %-40s %s' % (pre, k, t, d))
        if '$ref' in v:
            show_schema(deref(v['$ref']), indent + 1)
        if v.get('items') and '$ref' in v.get('items', {}):
            show_schema(deref(v['items']['$ref']), indent + 1)

for m, p in want:
    op = paths.get(p, {}).get(m)
    if not op:
        print('\n== %s %s -> NOT IN SPEC' % (m.upper(), p))
        continue
    print('\n=== %s %s | %s' % (m.upper(), p, op.get('operationId')))
    for pa in op.get('parameters', []):
        print('  param: %s %s %s' % (pa.get('in'), pa.get('name'), pa.get('required', '')))
    rb = op.get('requestBody', {})
    sch = None
    if rb:
        sch = rb.get('content', {}).get('application/json', {}).get('schema', {})
        if '$ref' in sch:
            sch = deref(sch['$ref'])
        print('  BODY:')
        show_schema(sch, 2)
    # 响应 200 schema
    resp = op.get('responses', {}).get('200', {})
    rsch = resp.get('content', {}).get('application/json', {}).get('schema', {})
    if '$ref' in rsch:
        rsch = deref(rsch['$ref'])
    if rsch and rsch != sch:
        print('  RESP200:')
        show_schema(rsch, 2)
