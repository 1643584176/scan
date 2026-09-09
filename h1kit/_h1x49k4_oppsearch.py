# -*- coding: utf-8 -*-
"""opportunities_search 500 根因诊断(匿名对照)"""
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
        print(f'--- {name} [{r.status_code} {dt}s] {r.text.replace(chr(10), " ")[:300]}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(2.5)

# 1. 无 query 参数(参数结构判别)
probe('R1 noquery', '{ opportunities_search(first: 1) { total_count } }')
# 2. 空 filter
probe('R2 emptyf', '{ opportunities_search(filter: {}, first: 1) { total_count } }')
# 3. multi_match 无 fields
probe('R3 mm_nof', '{ opportunities_search(query: { multi_match: { query: "a" } }, first: 1) { total_count } }')
# 4. qs 带 fields 通配
probe('R4 qs_wild', '{ opportunities_search(query: { query_string: { query: "a", fields: ["*"] } }, first: 1) { total_count } }')
# 5. qs 带 default_field
probe('R5 qs_def', '{ opportunities_search(query: { query_string: { query: "a", default_field: "title" } }, first: 1) { total_count } }')
# 6. sort 变体
probe('R6 sort', '{ opportunities_search(query: { query_string: { query: "a" } }, sort: [{ field: "handle", direction: ASC }], first: 1) { total_count } }')
