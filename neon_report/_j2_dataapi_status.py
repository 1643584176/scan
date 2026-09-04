# -*- coding: utf-8 -*-
"""Data API 状态探测:项目列表(org) + 分支 + data-api GET 现状"""
import json, os, sys, http.client, ssl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctx_data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID = ctx_data['pid']
BID = ctx_data['bid']
ORG = ctx_data['org']

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, timeout=25)
    hdrs = {'Cookie': cookie_str(), 'Content-Type': 'application/json'}
    hdrs.update(HEADERS_TEST)
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

print('ctx: pid=%s bid=%s org=%s' % (PID, BID, ORG))

st, body = req('GET', API_BASE + '/projects?org_id=%s&limit=50' % ORG)
print('\n=== 项目列表 status=%s ===' % st)
try:
    j = json.loads(body)
    for p in j.get('projects', []):
        print(' pid=%s name=%s state=%s' % (p.get('id'), p.get('name'), p.get('state')))
except Exception:
    print(body[:500])

st, body = req('GET', API_BASE + '/projects/%s/branches' % PID)
print('\n=== 分支 status=%s ===' % st)
try:
    j = json.loads(body)
    for b in j.get('branches', []):
        print(' bid=%s name=%s state=%s' % (b.get('id'), b.get('name'), b.get('state')))
except Exception:
    print(body[:500])

st, body = req('GET', API_BASE + '/projects/%s/branches/%s/databases' % (PID, BID))
print('\n=== 数据库 status=%s ===' % st)
try:
    j = json.loads(body)
    for d in j.get('databases', []):
        print(' db=%s owner=%s' % (d.get('name'), d.get('owner_name')))
except Exception:
    print(body[:500])

for db in ('neondb', 'postgres'):
    st, body = req('GET', API_BASE + '/projects/%s/branches/%s/data-api/%s' % (PID, BID, db))
    print('\n=== data-api GET %s status=%s ===' % (db, st))
    print(body[:600])
