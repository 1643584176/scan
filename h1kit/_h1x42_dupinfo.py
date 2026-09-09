# -*- coding: utf-8 -*-
"""h1x42: ReportDuplicateInformation 类型完整字段(includeDeprecated)+ 原报告元数据端点
终验:dup reporter 视角所有可读字段"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

q = '{ __type(name: "ReportDuplicateInformation") { fields(includeDeprecated: true) { name isDeprecated type { kind name ofType { kind name ofType { name } } } } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
j = r.json()
f = j.get('data', {}).get('__type')
if f:
    for x in f['fields']:
        t = x['type']
        tn = t['name'] or (t['ofType'] or {}).get('name') or '?'
        print(f"  {x['name']}{' [DEP]' if x.get('isDeprecated') else ''} : {tn}")
else:
    print(r.text[:400])
