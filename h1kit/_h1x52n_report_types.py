# -*- coding: utf-8 -*-
"""h1x52n: Report 字段类型表(找 dup/original 相关字段的返回类型 + 深挖候选)(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

q = '''query { __type(name: "Report") { fields { name type { kind name ofType { kind name ofType { kind name } } } } } }'''
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
j = r.json()
fields = j['data']['__type']['fields']
# 打印完整 名称->类型
for f in fields:
    t = f['type']
    tn = t.get('name') or (t.get('ofType') or {}).get('name') or ''
    print(f"{f['name']:<48} {tn}")
