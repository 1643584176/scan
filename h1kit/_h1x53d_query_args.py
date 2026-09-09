# -*- coding: utf-8 -*-
"""h1x53d: Query 根字段参数全枚举 - 找按 report_id 直查的入口(intake_workflow/conversation/draft 等)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

q = '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } }'''
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
d = r.json()
for f in d['data']['__type']['fields']:
    argnames = [a['name'] for a in f['args']]
    # 只打印含 id/report/team/intent/workflow/conversation/draft 类参数或名称相关的
    if any(k in f['name'].lower() for k in ('workflow', 'intake', 'conversation', 'draft', 'assistant', 'intent', 'report')) or \
       any(k in (a.lower() for a in argnames) for k in ('report_id', 'report_ids', 'database_id', 'intent_id')):
        print(f['name'], '=>', json.dumps(f['args'])[:400])
