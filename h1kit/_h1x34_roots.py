# -*- coding: utf-8 -*-
"""h1x34: E2 时代 introspection 的 Query 根字段未测项清理
(analytic_reports / users / teams / audit_log_items / hackerone_triagers / severities / cve_entries)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

# 匿名侧先看公开可达性(有公开数据也记录)
qs = {
    'AR1': '{ analytics_reports(first: 3) { total_count nodes { __typename id name } } }',
    'AR2': '{ analytics_reports(where: {name: {_like: "%a%"}}) { total_count nodes { __typename id name } } }',
    'US1': '{ users(first: 3) { total_count nodes { __typename } } }',
    'AL1': '{ audit_log_items(first: 3) { total_count } }',
    'HT1': '{ hackerone_triagers(first: 3) { total_count nodes { __typename } } }',
}
for k, q in qs.items():
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        print(f'=== {k} STATUS={r.status_code} ===')
        print(r.text[:600])
        print()
    except Exception as e:
        print(f'=== {k} ERR {e} ===')
