# -*- coding: utf-8 -*-
"""h1x49d: ReportOrderInput 结构 + Hasura 直连端点探测 + ES query_string 语法面"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

print('--- ReportOrderInput ---')
q = '{ __type(name: "ReportOrderInput") { inputFields { name type { kind name ofType { kind name ofType { name } } } } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
print(r.text[:900])
print()

print('--- Hasura/内部端点探测 ---')
paths = ['/v1/graphql', '/v1/query', '/graphql/v1', '/hasura/v1/graphql', '/api/graphql', '/gql', '/graphql/query', '/v2/query']
for p in paths:
    try:
        r = s.post('https://hackerone.com' + p, json={'query': '{ __typename }'}, timeout=12, allow_redirects=False)
        print(f'[{r.status_code}] {p} ct={r.headers.get("content-type","")[:30]} body={r.text[:80]}')
    except Exception as e:
        print(f'[ERR] {p} {type(e).__name__}')

print()
print('--- ES query_string 语法面(索引内查 _id) ---')
# ES query_string 语法:字段名:值
for idx, qs_ in [('CompleteHacktivityReportIndex', '_id:3732660'), ('CompleteHacktivityReportIndex', '_id:2487889'), ('CompleteHacktivityReportIndex', 'reporter.username:bate5a')]:
    q = '{ search(index: ' + idx + ', query_string: "' + qs_ + '") { total_count } }'
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        print(f'{idx} | {qs_} -> [{r.status_code}] {r.text[:200]}')
    except Exception as e:
        print(f'{idx} | {qs_} ERR {type(e).__name__}')
