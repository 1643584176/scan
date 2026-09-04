# -*- coding: utf-8 -*-
"""读 AI Gateway / Logs / Snapshot / Consumption / DataAPISettings 相关 schema 全貌"""
import json

d = json.load(open('_openapi_v2.json', encoding='utf-8'))
wanted = ['DataAPISettings', 'AIGateway', 'ai_gateway', 'Log', 'log', 'Snapshot', 'snapshot', 'Consumption', 'consumption', 'Storage']
seen = set()
for name, sch in d['components']['schemas'].items():
    low = name.lower()
    if any(w.lower() in low for w in ('aigateway', 'ai_gateway', 'logquery', 'logfields', 'snapshot', 'consumptionhistory', 'consumptionmetric')):
        print('SCHEMA %s:' % name)
        print(json.dumps(sch, ensure_ascii=False)[:900])
        print()
        seen.add(name)
