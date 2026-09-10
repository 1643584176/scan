# -*- coding: utf-8 -*-
"""匿名对照:analytics DSL 可读表(判别设计公开 vs 登录特权)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

W, E = '2026-01-01T00:00:00Z', '2026-12-31T23:59:59Z'

def probe(name, qstr, timeout=25):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        print(f'--- {name} [{r.status_code} {dt}s] {r.text.replace(chr(10), " ")[:300]}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(2.5)

base = ('{ analytics(queries: [{ uid: "a1", start_at: "%s", end_at: "%s", interval: year, '
        'from: %s, select: [{ field: %s, function: count, as: "cnt" }] }]) { uid keys values } }')

# 1. dim_surveys(调查模板)
probe('anon_surveys', base % (W, E, 'dim_surveys', 'dim_surveys__survey_id'))
# 2. fct_bounty_table_cohorts(bounty 基准)
probe('anon_cohorts', base % (W, E, 'fct_bounty_table_cohorts', 'fct_bounty_table_cohorts__sfdc_revenue_band'))
# 3. platform_benchmarks(global p50 键值)
probe('anon_pbench', base % (W, E, 'platform_benchmarks', 'platform_benchmarks__key'))
# 4. fct_platform_benchmarks
probe('anon_fpbench', base % (W, E, 'fct_platform_benchmarks', 'fct_platform_benchmarks__interval'))
# 5. dim_hacker_reports(对照:user 过滤表匿名应拒/空)
probe('anon_hreports', base % (W, E, 'dim_hacker_reports', 'dim_hacker_reports__report_id'))
