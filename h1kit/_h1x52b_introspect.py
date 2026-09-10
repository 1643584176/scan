# -*- coding: utf-8 -*-
"""h1x52b: introspect triage_inbox_items/assignable_teams 相关类型字段(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, query):
    r = s.post('https://hackerone.com/graphql', json={'query': query}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:2500])
    print()

# triage_inbox_items 参数与返回类型
probe('triage_arg', '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name } } } } type { kind name ofType { kind name } } } } }''')

# 具体类型字段
for tn in ['TriageInboxItem', 'TriageInboxItemConnection', 'AnalyticsReportConnection', 'GatewayUser', 'GatewayUserConnection']:
    probe('type_' + tn, '''query { __type(name: "%s") { kind name fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''' % tn)
