# -*- coding: utf-8 -*-
"""h1x49j: 读 search 节点完整字段(report/reporter/team),验证索引内容(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

NODES = 'nodes { ... on HacktivityDocument { report { id title } reporter { username } team { handle name } severity_rating public disclosed } }'

def search(name, qs, index='CompleteHacktivityReportIndex', timeout=20):
    q = 'query { search(index: %s, query_string: "%s", limit: 3) { total_count %s } }' % (index, qs.replace('"', '\\"'), NODES)
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=timeout)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:1200]}')
        return r.text
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')
        return None

search('nodes_bate5a', 'reporter:bate5a')
search('nodes_2487889', 'title:"Insecure Direct Object Reference"')
search('nodes_xxbo', 'reporter:xxbo')
search('nodes_neon', 'team:Neon')
