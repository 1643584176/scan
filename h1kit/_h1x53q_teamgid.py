# -*- coding: utf-8 -*-
"""h1x53q: 匿名拿 H1 自身/neon 的 Team gid(通过公开披露报告)"""
import json, sys, io, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def gql(q):
    req = urllib.request.Request('https://hackerone.com/graphql',
        data=json.dumps({'query': q}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__err': str(e)}

# H1 自身披露报告 2487889 的 team
q1 = 'query{ reports(where:{id:{_eq:2487889}}){ nodes{ id team{ id _id handle } } } }'
r1 = gql(q1)
print('H1 report 2487889:', json.dumps(r1.get('data'), ensure_ascii=False)[:400])

# neon 披露报告(取 1 条拿 team)
q2 = 'query{ reports(where:{team:{handle:{_eq:"neon_bbp"}} disclosed_at:{_is_null:false}}, first:1){ nodes{ id team{ id _id handle } } } }'
r2 = gql(q2)
print('neon disclosed:', json.dumps(r2.get('data'), ensure_ascii=False)[:400])

# teams 根查询直取(若允许)
q3 = 'query{ teams(where:{handle:{_in:["hackerone","neon_bbp"]}}){ nodes{ id _id handle } } }'
r3 = gql(q3)
print('teams root:', json.dumps(r3.get('data'), ensure_ascii=False)[:500])
if r3.get('errors'):
    print('errors:', json.dumps(r3['errors'], ensure_ascii=False)[:300])
