# -*- coding: utf-8 -*-
"""h1x52d: 精确查 search 字段全部参数类型(找 index 枚举/字符串;sort/reporter_filter 类型)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

q = '''query {
  __type(name: "Query") {
    fields {
      name
      args { name type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } }
    }
  }
}'''
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
j = r.json()
for f in j['data']['__type']['fields']:
    if f['name'] in ('search', 'activity', 'analytics', 'conversation'):
        print('FIELD', f['name'])
        for a in f['args']:
            print('  arg', a['name'], ':', json.dumps(a['type'])[:200])
        print()
