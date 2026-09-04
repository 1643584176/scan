# -*- coding: utf-8 -*-
"""看 ProjectCreateRequest.project 字段原始定义"""
import json
spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
s = spec['components']['schemas']['ProjectCreateRequest']
print(json.dumps(s, indent=1, ensure_ascii=False)[:2000])
# 找 project 相关的其他 schema
for n in spec['components']['schemas']:
    if 'project' in n.lower() and 'create' in n.lower() or n in ('Project', 'ProjectCreate'):
        print('SCHEMA:', n)
