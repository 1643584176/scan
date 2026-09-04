# -*- coding: utf-8 -*-
"""离线查未测端点 body schema (transfer/permissions/anonymize/shared)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec['paths']

want = [
    ('get', '/projects/shared'),
    ('post', '/projects/{project_id}/transfer_requests'),
    ('put', '/projects/{project_id}/transfer_requests/{request_id}'),
    ('post', '/users/me/projects/transfer'),
    ('post', '/organizations/{source_org_id}/projects/transfer'),
    ('get', '/projects/{project_id}/permissions'),
    ('post', '/projects/{project_id}/permissions'),
    ('get', '/projects/{project_id}/members'),
    ('put', '/projects/{project_id}/members/{member_id}/role'),
    ('post', '/projects/{project_id}/branches/{branch_id}/anonymize'),
    ('get', '/projects/{project_id}/branches/{branch_id}/anonymized_status'),
    ('get', '/projects/{project_id}/branches/{branch_id}/masking_rules'),
    ('patch', '/projects/{project_id}/branches/{branch_id}/masking_rules'),
    ('get', '/projects/{project_id}/branches/{branch_id}/backup_schedule'),
    ('get', '/projects/{project_id}/connection_uri'),
    ('post', '/projects/{project_id}/recover'),
    ('get', '/projects/{project_id}/advisors'),
]

schemas = spec['components']['schemas']

def deref(ref):
    if not ref:
        return None
    return schemas.get(ref.split('/')[-1])

for m, p in want:
    op = paths.get(p, {}).get(m)
    if not op:
        print('== %s %s -> NOT IN SPEC' % (m.upper(), p))
        continue
    print('\n== %s %s | %s' % (m.upper(), p, op.get('operationId')))
    params = op.get('parameters', [])
    for pa in params:
        print('  param: %s %s' % (pa.get('in'), pa.get('name')))
    rb = op.get('requestBody', {})
    if rb:
        content = rb.get('content', {}).get('application/json', {})
        sch = content.get('schema', {})
        if '$ref' in sch:
            sch = deref(sch['$ref'])
        if sch:
            props = sch.get('properties', {})
            reqs = sch.get('required', [])
            print('  body required:', reqs)
            for k, v in props.items():
                t = v.get('type', v.get('$ref', v.get('example', v.get('enum', ''))))
                desc = str(v.get('description', ''))[:90]
                print('    %-28s %-36s %s' % (k, t, desc))
