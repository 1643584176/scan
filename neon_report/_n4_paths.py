# -*- coding: utf-8 -*-
"""列出 OpenAPI 中 functions/buckets/credentials 相关端点与 operations"""
import json
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
for k in sorted(d['paths'].keys()):
    if any(s in k for s in ('function', 'credential', 'bucket')):
        ops = ','.join(m.upper() for m in d['paths'][k] if m in ('get', 'post', 'put', 'delete', 'patch'))
        print('%-110s [%s]' % (k, ops))
