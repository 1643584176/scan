# -*- coding: utf-8 -*-
"""h1x37: User 类型字段全量(includeDeprecated)+ 找 User 上报告相关字段"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

q = '{ __type(name: "User") { fields(includeDeprecated: true) { name isDeprecated args { name } } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
j = r.json()
f = j.get('data', {}).get('__type')
if not f:
    print(r.text[:500])
else:
    names = [(x['name'], x.get('isDeprecated'), [a['name'] for a in x.get('args') or []]) for x in f.get('fields') or []]
    print(f'total {len(names)} fields')
    for n, dep, args in names:
        print(f'  {n}{" [DEP]" if dep else ""} {args if args else ""}')
