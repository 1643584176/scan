# -*- coding: utf-8 -*-
"""h1x52h: introspect NotificationDocument/ReportDocument/TermsFilterInput/BoolQueryInput(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:4000])
    print()

# 对象类型字段(含类型展开一层)
for tn in ['NotificationDocument', 'ReportDocument', 'StoredQueryDocument', 'OpportunityDocument']:
    probe('type_' + tn, '''query { __type(name: "%s") { kind fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''' % tn)

# 输入类型字段
for tn in ['TermsFilterInput', 'BoolQueryInput', 'RangeInput', 'NestedInput']:
    probe('input_' + tn, '''query { __type(name: "%s") { kind inputFields { name type { kind name ofType { kind name ofType { kind name } } } } } }''' % tn)
