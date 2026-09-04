# -*- coding: utf-8 -*-
"""dump 创建类操作的参数/body 定义(建项目/分支/DataAPI/Bucket/Credential/Function)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comps = spec['components']['schemas']
paths = spec['paths']

TARGET = [
    ('/projects', 'post'),
    ('/projects/{project_id}/branches', 'post'),
    ('/projects/{project_id}/branches/{branch_id}/data-api/{database_name}', 'post'),
    ('/projects/{project_id}/branches/{branch_id}/buckets', 'post'),
    ('/projects/{project_id}/branches/{branch_id}/credentials', 'post'),
    ('/projects/{project_id}/branches/{branch_id}/functions', 'post'),
]

def resolve_body(ref):
    name = ref.split('/')[-1]
    s = comps.get(name, {})
    print('    SCHEMA %s:' % name)
    if s.get('properties'):
        for pn, pv in s['properties'].items():
            req = 'REQ' if pn in s.get('required', []) else 'opt'
            if '$ref' in pv:
                rn = pv['$ref'].split('/')[-1]
                rs = comps.get(rn, {})
                print('      - %s (%s) -> %s %s %s' % (pn, req, rn, rs.get('type'), (rs.get('enum') or rs.get('description') or '')[:80]))
            else:
                print('      - %s (%s) %s %s %s' % (pn, req, pv.get('type'), pv.get('enum') or '', (pv.get('description') or '')[:80]))
    else:
        print('      raw:', json.dumps(s)[:200])

for p, m in TARGET:
    op = paths.get(p, {}).get(m)
    if not op:
        print('== %s %s NOT FOUND' % (m.upper(), p))
        continue
    print('\n== %s %s :: %s' % (m.upper(), p, op.get('operationId')))
    for prm in op.get('parameters', []):
        print('  PARAM %s %s %s %s' % (prm.get('in'), prm.get('name'), 'REQ' if prm.get('required') else 'opt',
                                        json.dumps(prm.get('schema', {}))[:120]))
    rb = op.get('requestBody')
    if rb:
        for ct, v in (rb.get('content') or {}).items():
            if '$ref' in v.get('schema', {}):
                resolve_body(v['schema']['$ref'])
            else:
                print('  BODY raw:', json.dumps(v.get('schema'))[:300])
    # 响应 schema 里找 url/id 字段
    r200 = op.get('responses', {}).get('200') or op.get('responses', {}).get('201')
    if r200:
        for ct, v in (r200.get('content') or {}).items():
            if '$ref' in v.get('schema', {}):
                print('  RESP schema:', v['schema']['$ref'].split('/')[-1])
