# -*- coding: utf-8 -*-
"""h1x53g: Query 根字段全量 dump(匿名 introspection) - 找所有按 id/直查型入口"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

q = '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } }'''
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
d = r.json()
out = []
for f in d['data']['__type']['fields']:
    if f['args']:
        a = '; '.join('%s:%s' % (x['name'], (x['type'].get('name') or x['type'].get('ofType', {}).get('name') or '?') if x['type']['kind'] != 'LIST' else 'LIST') for x in f['args'])
        out.append('%-55s | %s' % (f['name'], a))
with open(r'D:\scan\h1kit\_h1x53g_query_roots.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(out))
print('total fields with args:', len(out))
for line in out:
    print(line)
