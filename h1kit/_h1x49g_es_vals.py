# -*- coding: utf-8 -*-
"""h1x49g: ES 字段值格式枚举 + 500 复现 + search 节点结构探测(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def search(name, qs, fields='total_count', index='CompleteHacktivityReportIndex', timeout=20):
    q = '{ search(index: %s, query_string: "%s", limit: 3) { %s } }' % (index, qs.replace('"', '\\"'), fields)
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=timeout)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:400]}')
        return r.text
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')
        return None

# 1. 500 复现(disclosed_at 通配)
for i in range(3):
    search(f'disclosed_2024_rep{i}', 'disclosed_at:2024*')
search('disclosed_gt', 'disclosed_at:>2024-01-01')
search('disclosed_range', 'disclosed_at:[2024-01-01 TO 2024-12-31]')

# 2. team 值格式
for v in ['HackerOne', 'hackerone', 'Neon', 'neon', 'neon_bbp', 'Security', 'security', 'Netlify', 'shopify']:
    search('team_' + v, 'team:' + v)

# 3. substate 值格式
for v in ['resolved', 'Resolved', 'informative', 'Informative', 'duplicate', 'new', 'pending', 'not_applicable', 'triaged']:
    search('sub_' + v, 'substate:' + v)

# 4. cwe 值格式
for v in ['79', 'CWE-79', '79.0', '79.0.0', 'CWE79']:
    search('cwe_' + v, 'cwe:' + v)

# 5. search 节点结构(看返回对象字段)
search('nodes_probe', 'severity_rating:high', fields='nodes { __typename }')
search('nodes_fields', 'severity_rating:high', fields='nodes { id title }')
