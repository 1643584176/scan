# -*- coding: utf-8 -*-
"""dump CreateCredentialRequest/CreateCredentialResponse/CredentialSecret 完整定义 + credentials 端点 operationId"""
import json
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
s = d['components']['schemas']
for t in ('CreateCredentialRequest', 'CreateCredentialResponse', 'CredentialSecret'):
    if t in s:
        print('=' * 20, t)
        print(json.dumps(s[t], indent=1)[:3000])
# 端点 operationId
for k in sorted(d['paths']):
    if 'credentials' in k:
        for m, v in d['paths'][k].items():
            if m in ('get', 'post', 'delete', 'put'):
                print('%-80s %s -> %s' % (k, m.upper(), v.get('operationId', v.get('summary', ''))[:60]))
