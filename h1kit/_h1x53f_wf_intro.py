# -*- coding: utf-8 -*-
"""h1x53f: FiltersWorkflowRunFilterInput + WorkflowStepRun 字段 + output JSON 结构(匿名 introspection)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=6000):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

probe('wf_filter', '''query { __type(name: "FiltersWorkflowRunFilterInput") { inputFields { name type { kind name ofType { kind name ofType { kind name } } } } } }''')
probe('step_run', '''query { __type(name: "WorkflowStepRun") { kind fields { name type { kind name ofType { kind name } } } } }''')
probe('step_conn', '''query { __type(name: "WorkflowStepRunConnection") { kind fields { name } } }''')
probe('wf_run_conn', '''query { __type(name: "WorkflowRunConnection") { kind fields { name } } }''')
