# -*- coding: utf-8 -*-
"""dump 共享项目/项目成员 schema + /projects/shared 响应结构"""
import json
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
s = d['components']['schemas']
for t in sorted(s):
    if any(x in t.lower() for x in ('sharedproject', 'projectmember', 'memberrole', 'projectrole')):
        print('=' * 20, t)
        print(json.dumps(s[t], indent=1)[:1500])
