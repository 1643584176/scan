# -*- coding: utf-8 -*-
"""h1x52e: index 类型展开 + QueryInput/SortInput/ReporterFilter 字段(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def gql(q):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=30)
    return r.text

# index 参数类型 4 层展开
q1 = '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } } }'''
t = gql(q1)
try:
    j = json.loads(t)
    for f in j['data']['__type']['fields']:
        if f['name'] == 'search':
            for a in f['args']:
                if a['name'] in ('index', 'query', 'sort'):
                    print('ARG', a['name'], json.dumps(a['type']))
except Exception as e:
    print('E1', e, t[:300])

# 枚举值(如果 index 是枚举,直接查 __type)
for tn in ['SearchIndex', 'IndexName', 'ReportIndex']:
    q2 = '''query { __type(name: "%s") { kind name enumValues { name } } }''' % tn
    t2 = gql(q2)
    print('TYPE', tn, ':', t2[:600])

# QueryInput / SortInput 输入字段
for tn in ['QueryInput', 'SortInput', 'AnalyticsQueryInputType']:
    q3 = '''query { __type(name: "%s") { kind name inputFields { name type { kind name ofType { kind name } } } } }''' % tn
    t3 = gql(q3)
    print('INP', tn, ':', t3[:1500])
