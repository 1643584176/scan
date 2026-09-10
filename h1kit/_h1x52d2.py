# -*- coding: utf-8 -*-
"""h1x52d2: 查 search 参数类型(简化,先看报错)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

q = '''query { __type(name: "Query") { fields { name args { name type { kind name } } } } }'''
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
print('status', r.status_code)
t = r.text
print(t[:500])
try:
    j = r.json()
    fields = j['data']['__type']['fields']
    for f in fields:
        if f['name'] == 'search':
            for a in f['args']:
                print('  arg', a['name'], ':', a['type'])
except Exception as e:
    print('ERR', e)
