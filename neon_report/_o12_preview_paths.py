# -*- coding: utf-8 -*-
"""Preview tag 路径 + 实测 Functions 端点(控制面)"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
print('=== Preview tag paths ===')
for p, ops in paths.items():
    for m, op in ops.items():
        if isinstance(op, dict) and 'Preview' in (op.get('tags') or []):
            print(' %s %s | %s' % (m.upper(), p, op.get('summary', '')))
