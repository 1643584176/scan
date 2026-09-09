# -*- coding: utf-8 -*-
"""h1x12: 匿名批量查已知报告编号可见性"""
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

IDS = ['242816', '2487889', '3732660', '3951926', '3954985', '3955363', '3965216', '3972961', '3992341']

def gql(q):
    r = s.post('https://hackerone.com/graphql', json={'query': q, 'variables': {}}, timeout=25)
    try:
        return r.json()
    except Exception:
        return {'raw': r.text[:200]}

for rid in IDS:
    j = gql(f'query {{ reports(where: {{id: {{_eq: {rid}}}}}) {{ nodes {{ _id title state substate created_at disclosed_at reporter {{ username name }} team {{ name handle }} }} }} }}')
    if 'errors' in j:
        print(f'[{rid}] ERR {json.dumps(j["errors"])[:150]}')
    else:
        nodes = j.get('data', {}).get('reports', {}).get('nodes', [])
        if not nodes:
            print(f'[{rid}] EMPTY (私有或不存在)')
        else:
            n = nodes[0]
            print(f'[{rid}] VISIBLE title={n.get("title")!r} state={n.get("state")} disclosed_at={n.get("disclosed_at")} reporter={n.get("reporter")} team={n.get("team")}')
