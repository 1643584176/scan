# -*- coding: utf-8 -*-
"""h1x39: Query 根字段全量落盘(includeDeprecated)+ 参数,逐字段筛未测项"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
q = '{ __type(name: "Query") { fields(includeDeprecated: true) { name isDeprecated args { name type { kind name ofType { kind name } } } type { kind name ofType { kind name } } } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
j = r.json()
rows = []
for f in j['data']['__type']['fields']:
    rt = f['type']
    rn = rt['name'] or (rt['ofType'] or {}).get('name') or ((rt['ofType'] or {}).get('ofType') or {}).get('name') or '?'
    args = ','.join(a['name'] for a in f.get('args') or [])
    rows.append((f['name'], 'DEP' if f.get('isDeprecated') else '', rn, args))
txt = '\n'.join(f'{n}\t{d}\t{t}\t{a}' for n, d, t, a in rows)
open(r'D:\scan\h1kit\_h1x39_query_roots.txt', 'w', encoding='utf-8').write(txt)
print(f'total {len(rows)}')
print(txt)
