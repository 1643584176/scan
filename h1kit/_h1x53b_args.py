# -*- coding: utf-8 -*-
"""h1x53b: 未测 team 数据候选参数类型 + org/team gid 获取(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=1800):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

# 候选字段的参数类型(在 Query 类型上)
probe('args2', '''query { __type(name: "Query") { fields { name args { name type { kind name ofType { kind name ofType { kind name } } } } } } }''', 6000)
# org/team gid(匿名公开?)
probe('org_id', '''query { organization(handle: "neon") { id } }''')
probe('team_id', '''query { team(handle: "neon_bbp") { id organization { id } } }''')
probe('team_vercel', '''query { team(handle: "vercel_sandbox") { id organization { id } } }''')
