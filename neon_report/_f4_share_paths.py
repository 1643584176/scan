# -*- coding: utf-8 -*-
"""查 OpenAPI:分支分享/共享/shared 相关端点(评估跨分支凭据操作的权限边界)"""
import json
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
for k in sorted(d['paths']):
    if any(s in k.lower() for s in ('share', 'invite', 'member', 'role')):
        for m, v in d['paths'][k].items():
            if m in ('get', 'post', 'put', 'delete', 'patch'):
                print('%-90s %s -> %s' % (k, m.upper(), (v.get('operationId') or v.get('summary') or '')[:70]))
