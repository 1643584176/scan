# -*- coding: utf-8 -*-
"""查 OpenAPI 中 transfer/ownership 相关路径与 transfer_status 定义"""
import json
d = json.load(open('_openapi_v2.json', encoding='utf-8'))
for p, v in d['paths'].items():
    if 'transfer' in p.lower() or 'owner' in p.lower():
        methods = [m.upper() for m in v.keys() if m in ('get', 'post', 'put', 'patch', 'delete')]
        print(p, methods)
# transfer_status 定义上下文
for name, sch in d['components']['schemas'].items():
    if 'transfer' in name.lower() or 'Transfer' in name:
        print('\nSCHEMA:', name)
        print(json.dumps(sch, ensure_ascii=False)[:600])
