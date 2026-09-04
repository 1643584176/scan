# -*- coding: utf-8 -*-
"""离线:transfer_ownership + transfer_requests 完整响应与错误码"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comp = spec['components']['schemas']

for p in ['/projects/auth/transfer_ownership', '/projects/{project_id}/transfer_requests',
          '/projects/{project_id}/transfer_requests/{request_id}']:
    for m in ('post', 'put', 'get', 'delete'):
        op = spec['paths'].get(p, {}).get(m)
        if not op:
            continue
        print('\n== %s %s | %s' % (m.upper(), p, op.get('summary', '')), flush=True)
        for code, resp in op.get('responses', {}).items():
            desc = resp.get('description', '')
            rref = resp.get('content', {}).get('application/json', {}).get('schema', {}).get('$ref', '')
            print('  %s: %s ref=%s' % (code, desc[:120], rref), flush=True)
            if rref:
                nm = rref.split('/')[-1]
                sch = comp.get(nm, {})
                for k, v in sch.get('properties', {}).items():
                    rr = v.get('$ref', '') or v.get('items', {}).get('$ref', '')
                    print('     %s: type=%s ref=%s | %s' % (k, v.get('type'), rr, v.get('description', '')[:120]), flush=True)
        # 找 4xx 错误描述
        for code, resp in op.get('responses', {}).items():
            if code.startswith('4') or code.startswith('5'):
                c = resp.get('content', {}).get('application/json', {})
                for k2, v2 in c.items():
                    if k2 == 'schema':
                        rr = v2.get('$ref', '')
                        if rr:
                            nm = rr.split('/')[-1]
                            sch = comp.get(nm, {})
                            if sch.get('properties', {}).get('errors'):
                                for e in sch['properties']['errors'].get('items', {}).get('properties', {}).get('code', {}).get('enum', []):
                                    print('     errcode:', e, flush=True)
