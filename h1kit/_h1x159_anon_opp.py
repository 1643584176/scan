# -*- coding: utf-8 -*-
"""匿名对照:OpportunitiesIndex 是否匿名可查(判别登录特权 vs 公开设计)
对照:匿名 vs 登录(需 cookie——先用匿名;登录对照由 console 完成)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, qstr):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=20)
        dt = round(time.time() - t0, 1)
        print(f'--- {name} [{r.status_code} {dt}s] {r.text[:400]}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')

# 1. 匿名搜 OpportunitiesIndex 量级
probe('anon_opp_count', '{ search(index: OpportunitiesIndex, query_string: "*", limit: 1) { total_count } }')
# 2. 匿名读 assa_abloy 全文
probe('anon_opp_doc', '{ search(index: OpportunitiesIndex, query_string: "assa_abloy_americas", limit: 1) { nodes { ... on OpportunityDocument { handle name state offers_bounties triage_active cached_response_efficiency_percentage first_response_time resolved_report_count gold_standard h1_clear credentials_set_up idv } } } }')
# 3. 匿名 range 过滤
probe('anon_opp_range', '{ search(index: OpportunitiesIndex, query: { range: { cached_response_efficiency_percentage: { gte: 95 } } }, limit: 2) { total_count nodes { ... on OpportunityDocument { handle } } } }')
# 4. 匿名查 NotificationsIndex(对照——通知应需登录)
probe('anon_notif', '{ search(index: NotificationsIndex, query_string: "*", limit: 1) { total_count } }')
# 5. 匿名查 CompleteHacktivity(正对照——公开索引应可用)
probe('anon_hacktivity', '{ search(index: CompleteHacktivityReportIndex, query_string: "IDOR", limit: 1) { total_count } }')
