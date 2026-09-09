# -*- coding: utf-8 -*-
"""h1x41: 查 participant 账号属性(h1_analyst_zenitsu / hackerone-agent)
假设:系统/AI 账号可能有公开的 team/membership 信息"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

fields = 'username name bio system hackerone_employee hackerone_agent hackerone_triager demo_hacker member_of_any_team member_of_any_organization verified cleared'
qs = {
    'A1_zenitsu': f'{{ user(username: "h1_analyst_zenitsu") {{ {fields} }} }}',
    'A2_agent': f'{{ user(username: "hackerone-agent") {{ {fields} }} }}',
    'A3_me': f'{{ user(username: "xxbo") {{ {fields} }} }}',
    'A4_zenitsu_teams': '{ user(username: "h1_analyst_zenitsu") { memberships(first: 10) { total_count nodes { __typename } } teams(first: 10) { total_count nodes { handle } } } }',
}
for k, q in qs.items():
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        print(f'=== {k} STATUS={r.status_code} ===')
        print(r.text[:1000])
        print()
    except Exception as e:
        print(f'=== {k} ERR {e} ===')
