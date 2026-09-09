# -*- coding: utf-8 -*-
"""h1x52l: 公开报告 2487889 的 activities 连接 + cloned_from/original 字段验证(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=2000):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

# 1. 公开报告 activities 连接(拿公开活动 id)
probe('pub_activities', '''query { report(id: 2487889) { id activities(first: 30) { edges { node { __typename id } } } } }''')
# 2. cloned_from / clones / original 系字段可用性
probe('pub_clones', '''query { report(id: 2487889) { id cloned_from { id title } clones(first: 5) { edges { node { id title } } } } }''')
# 3. Report 类型里 original 相关字段名
probe('report_orig_fields', '''query { __type(name: "Report") { fields { name } } }''', 6000)
