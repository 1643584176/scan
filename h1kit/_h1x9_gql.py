# -*- coding: utf-8 -*-
"""h1x9: 匿名探测 /graphql (Hasura 特征/错误形状/可达性)"""
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

queries = [
    ('introspection-query', '{ __schema { queryType { name } } }'),
    ('report-peek', 'query { reports(where: {id: {_eq: 2487889}}) { nodes { id } } }'),
    ('me', '{ me { id username } }'),
]
for tag, q in queries:
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q, 'variables': {}}, timeout=25)
        print(f'[{tag}] POST /graphql -> {r.status_code}')
        print('  headers:', {k: v for k, v in r.headers.items() if k.lower() in ('content-type', 'x-hasura', 'server', 'x-request-id')})
        print('  body:', r.text[:400])
    except Exception as e:
        print(f'[{tag}] ERR {type(e).__name__}: {e}')
    print()

# GET 形状
try:
    r = s.get('https://hackerone.com/graphql?query=%7B%20me%20%7B%20id%20%7D%20%7D', timeout=25)
    print(f'[get] GET /graphql -> {r.status_code} :: {r.text[:300]}')
except Exception as e:
    print('GET ERR', e)
