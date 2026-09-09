# -*- coding: utf-8 -*-
"""h1x49k3c: reporter_filter 值语义 + cwe_id 解析容忍 + disclosed_at 500 诊断(匿名,慢速)"""
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

def jd(v):
    return json.dumps(v, ensure_ascii=False)

# ===== 1. reporter_filter 语义判别(term vs query_string 拼接) =====
probe('RF_base', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", reporter_filter: "bate5a", limit: 1) { total_count } }')
probe('RF_or', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", reporter_filter: "bate5a OR zzz_nonexistent_9f3k", limit: 1) { total_count } }')
probe('RF_wild', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", reporter_filter: "*", limit: 1) { total_count } }')
probe('RF_quote', '{ search(index: CompleteHacktivityReportIndex, query_string: "*", reporter_filter: "bate5a\\" OR zzz", limit: 1) { total_count } }')
probe('RF_qs_mix', '{ search(index: CompleteHacktivityReportIndex, query_string: "title:IDOR", reporter_filter: "bate5a", limit: 1) { total_count } }')

# ===== 2. cwe_entry id 格式解析容忍(Ruby to_i 判别) =====
for v in ['CWE-89', '89', 'cwe-89', 'CWE-89x', '89x', 'x89', '79', 'CWE-79']:
    probe('CWE1 ' + v, '{ cwe_entry(cwe_id: %s) { id } }' % jd(v))
for v in ['CVE-2014-0160', '2014-0160', 'CVE-2014-0160x', 'x2014-0160']:
    probe('CVE1 ' + v, '{ cve_entry(cve_id: %s) { id } }' % jd(v))

# ===== 3. disclosed_at 500 根因诊断 =====
probe('DA_range', '{ search(index: CompleteHacktivityReportIndex, query_string: "disclosed_at:[2024-01-01 TO 2024-12-31]", limit: 1) { total_count } }')
probe('DA_pref', '{ search(index: CompleteHacktivityReportIndex, query_string: "disclosed_at:2024*", limit: 1) { total_count } }')
probe('DA_plain', '{ search(index: CompleteHacktivityReportIndex, query_string: "disclosed_at:2024-06-15", limit: 1) { total_count } }')
