# -*- coding: utf-8 -*-
"""h1x49h: search 节点 fragment 读取 + 索引内容最终验证(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

FRAG = '''fragment HD on HacktivityDocument { id title }'''
NODES = 'nodes { ... on HacktivityDocument { id title } }'

def search(name, qs, index='CompleteHacktivityReportIndex', timeout=20):
    q = 'query { search(index: %s, query_string: "%s", limit: 3) { total_count %s } }' % (index, qs.replace('"', '\\"'), NODES)
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=timeout)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:600]}')
        return r.text
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')
        return None

# 1. bate5a 节点(公开 27 条,验证字段与 id)
search('nodes_bate5a', 'reporter:bate5a')
# 2. 2487889 标题短语命中验证
search('nodes_2487889', 'title:"Insecure Direct Object Reference"')
# 3. xxbo 再确认
search('nodes_xxbo', 'reporter:xxbo')
# 4. severity high + substate duplicate 组合
search('nodes_high_dup', 'severity_rating:high AND substate:duplicate')
# 5. Neon team 节点
search('nodes_neon', 'team:Neon')
