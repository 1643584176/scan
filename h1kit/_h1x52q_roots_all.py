# -*- coding: utf-8 -*-
"""h1x52q: 完整根查询枚举(对照已测 23 项找未测面)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

r = s.post('https://hackerone.com/graphql', json={'query': '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name } } } } type { kind name ofType { kind name ofType { kind name } } } } } }'''}, timeout=30)
j = r.json()
if 'data' not in j:
    print(j)
    raise SystemExit
fields = j['data']['__type']['fields']
print(f'total root query fields: {len(fields)}')
for f in sorted(fields, key=lambda x: x['name']):
    t = f['type']
    tn = t.get('name') or (t.get('ofType') or {}).get('name') or ''
    args = ','.join(a['name'] for a in f.get('args') or [])
    print(f"{f['name']:<52} -> {tn:<40} args: {args}")
