# -*- coding: utf-8 -*-
"""细读候选面端点的 spec 细节(参数/schema/security)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec['paths']

INTEREST = [
    # (tag 关键词, 说明)
    ('functions', 'Functions 面'),
    ('buckets', 'Buckets 存储面'),
    ('presign', 'presign'),
    ('custom-domains', '自定义域名'),
    ('webhooks', 'Auth webhook'),
    ('auth/domains', 'redirect whitelist'),
    ('auth/users', 'auth user role'),
    ('credentials', 'credentials'),
    ('reveal', 'reveal'),
    ('finalize_restore', 'finalize'),
    ('transfer', 'transfer'),
    ('ai_gateway', 'AI Gateway'),
    ('available_preload', 'preload libs'),
    ('data-api', 'DataAPI'),
    ('reset_password', 'reset pw'),
    ('snapshots', 'snapshot'),
]

def dump_op(p, m, o):
    print('\n### %s %s :: %s' % (m.upper(), p, o.get('operationId')))
    print('  desc:', (o.get('description') or o.get('summary') or '')[:220].replace('\n', ' '))
    # 参数
    for prm in o.get('parameters', []):
        sch = prm.get('schema', {})
        req = 'REQ' if prm.get('required') else 'opt'
        print('  PARAM %s %s (%s) %s' % (prm.get('in'), prm.get('name'), req, json.dumps(sch)[:140]))
    # body
    rb = o.get('requestBody')
    if rb:
        for ct, v in (rb.get('content') or {}).items():
            print('  BODY[%s]: %s' % (ct, json.dumps(v.get('schema', {}))[:400]))
    # security
    print('  SEC:', o.get('security'))
    # 响应 code 集
    print('  RESP:', sorted(o.get('responses', {}).keys()))

seen = set()
for p in sorted(paths):
    for m, o in paths[p].items():
        if not isinstance(o, dict) or 'operationId' not in o:
            continue
        low = p.lower() + ' ' + o.get('operationId', '').lower()
        if any(k in low for k in ['function', 'bucket', 'presign', 'custom-domain', 'webhook',
                                  'auth/domains', 'auth/users', 'credential', 'reveal', 'finalize_restore',
                                  'transfer', 'ai_gateway', 'preload', 'data-api', 'reset_password',
                                  'snapshot']):
            if o['operationId'] in seen: continue
            seen.add(o['operationId'])
            dump_op(p, m, o)
