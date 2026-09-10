# -*- coding: utf-8 -*-
"""h1x52k: Report 类型 activities 连接 + ActivitiesComment 字段 + 公开报告活动 id 获取(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=1200):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

# 1. Report 类型 activities/activity 相关字段
probe('report_fields', '''query { __type(name: "Report") { fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''', 5000)
