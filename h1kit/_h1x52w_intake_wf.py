# -*- coding: utf-8 -*-
"""h1x52w: intake_workflow(report_id) 参数类型 + WorkflowRun 字段 + 匿名试探(只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=2500):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

# 1. Query.intake_workflow 参数类型
probe('intake_args', '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name } } } } } }''', 300)
# 2. WorkflowRun 字段
probe('workflow_run', '''query { __type(name: "WorkflowRun") { kind fields { name type { kind name ofType { kind name } } } } }''')
# 3. 匿名试探 intake_workflow(公开报告)
probe('iw_pub', '''query { intake_workflow(report_id: 2487889) { id state } }''')
# 4. WorkflowRunConnection 类型名确认(workflow_runs 根查询返回什么)
probe('wf_conn', '''query { __type(name: "WorkflowRunConnection") { kind fields { name } } }''')
