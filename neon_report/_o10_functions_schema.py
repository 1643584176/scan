# -*- coding: utf-8 -*-
"""Functions tag 端点完整 schema(参数+body 定义)"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
schemas = d.get('components', {}).get('schemas', {})

def resolve(ref):
    return schemas.get(ref.split('/')[-1], {})

fpaths = [
    ('GET', '/projects/{project_id}/branches/{branch_id}/functions'),
    ('GET', '/projects/{project_id}/branches/{branch_id}/functions/{slug}'),
    ('PATCH', '/projects/{project_id}/branches/{branch_id}/functions/{slug}'),
    ('DELETE', '/projects/{project_id}/branches/{branch_id}/functions/{slug}'),
    ('POST', '/projects/{project_id}/branches/{branch_id}/functions/{slug}/deployments'),
    ('GET', '/projects/{project_id}/branches/{branch_id}/custom-domains'),
    ('POST', '/projects/{project_id}/branches/{branch_id}/custom-domains'),
    ('DELETE', '/projects/{project_id}/branches/{branch_id}/custom-domains/{domain}'),
]

for want_m, want_p in fpaths:
    op = paths.get(want_p, {}).get(want_m.lower())
    if not op:
        print('MISSING %s %s' % (want_m, want_p))
        continue
    print('=' * 80)
    print('%s %s  %s' % (want_m, want_p, op.get('summary', '')))
    print('  desc:', (op.get('description') or '')[:200].replace('\n', ' '))
    for prm in op.get('parameters', []):
        sch = prm.get('schema', {})
        if '$ref' in sch:
            sch = resolve(sch['$ref'])
        print('  param: %s %s %s default=%s enum=%s' % (
            prm.get('in'), prm.get('name'), prm.get('required', False),
            sch.get('default'), sch.get('enum')))
    rb = op.get('requestBody', {})
    if rb:
        content = rb.get('content', {})
        for ct, cdef in content.items():
            sch = cdef.get('schema', {})
            if '$ref' in sch:
                sch = resolve(sch['$ref'])
            print('  body(%s) required=%s:' % (ct, rb.get('required')))
            print('   ', json.dumps(sch)[:600])
    # 响应示例
    for code, rdef in (op.get('responses') or {}).items():
        if code.startswith('2'):
            cont = rdef.get('content', {})
            for ct, cdef in cont.items():
                sch = cdef.get('schema', {})
                if '$ref' in sch:
                    sch = resolve(sch['$ref'])
                print('  resp %s %s: %s' % (code, ct, json.dumps(sch)[:400]))
