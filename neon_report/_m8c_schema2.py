# -*- coding: utf-8 -*-
"""ProjectBranchLogsQueryRequest / BranchStorage schema"""
import json

d = json.load(open('_openapi_v2.json', encoding='utf-8'))
for name in ('ProjectBranchLogsQueryRequest', 'ProjectBranchLogsQueryResponse', 'BranchStorage',
             'ProjectBranchLogFieldValuesResponse'):
    sch = d['components']['schemas'].get(name)
    print('=== %s ===' % name)
    print(json.dumps(sch, ensure_ascii=False)[:1400] if sch else 'NOT FOUND')
    print()
