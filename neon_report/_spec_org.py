# -*- coding: utf-8 -*-
"""离线 dump 组织/协作/计费相关 paths"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))

KWS = ['org', 'invit', 'member', 'billing', 'shared', 'transfer', 'collaborat', 'owner', 'partner',
       'store', 'api-key', 'apikey', 'webhook', 'subscription', 'plan', 'team', 'usage', 'me']

seen = set()
for p in sorted(spec['paths']):
    pl = p.lower()
    if not any(k in pl for k in KWS):
        continue
    for m in spec['paths'][p]:
        if m not in ('get', 'post', 'patch', 'put', 'delete'):
            continue
        op = spec['paths'][p][m]
        oid = op.get('operationId', '')
        if oid in seen:
            continue
        seen.add(oid)
        tag = (op.get('tags') or ['?'])[0]
        print('%-8s %-38s %-62s tag=%s' % (m.upper(), oid[:38], p, tag))
