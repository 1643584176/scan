# -*- coding: utf-8 -*-
"""查 anonymize/branch_anonymized spec 细节"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec['paths']

def show(m, p):
    op = paths.get(p, {}).get(m)
    if not op:
        print('NOT IN SPEC', m, p)
        return
    print('==', m.upper(), p, '|', op.get('operationId'))
    print(' desc:', str(op.get('description'))[:500])
    print(' params:', [(x.get('in'), x.get('name'), x.get('required'), str(x.get('schema', {}).get('example', ''))[:60])
                       for x in op.get('parameters', [])])
    rb = op.get('requestBody', {})
    if rb:
        print(' body:', json.dumps(rb.get('content', {}).get('application/json', {}).get('schema', {}), ensure_ascii=False)[:700])
    for code in ('200', '201', '202', '400', '404'):
        resp = op.get('responses', {}).get(code, {})
        if resp:
            sc = resp.get('content', {}).get('application/json', {}).get('schema', {})
            print(' resp%s:' % code, json.dumps(sc, ensure_ascii=False)[:250])
    print()

show('post', '/projects/{project_id}/branch_anonymized')
show('post', '/projects/{project_id}/branches/{branch_id}/anonymize')
show('get', '/projects/{project_id}/branches/{branch_id}/anonymized_status')
show('get', '/projects/{project_id}/branches/{branch_id}/masking_rules')
show('patch', '/projects/{project_id}/branches/{branch_id}/masking_rules')
