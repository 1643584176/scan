# -*- coding: utf-8 -*-
"""Data API 面侦察:OpenAPI 路径/schema + 项目/分支定位 + 启用状态"""
import json, glob, os, http.client, ssl

# 1) OpenAPI 路径
spec_path = None
for p in glob.glob(r'D:\scan\neon_report\_openapi*.json'):
    spec_path = p
    print('spec file:', p)
if spec_path:
    d = json.load(open(spec_path, encoding='utf-8'))
    print('\n=== data-api 相关路径 ===')
    for k in sorted(d.get('paths', {})):
        if 'data-api' in k.lower() or 'subzero' in k.lower():
            ops = list(d['paths'][k].keys())
            print(' ', k, ops)
    print('\n=== data-api 相关 schema ===')
    for n in sorted(d.get('components', {}).get('schemas', {})):
        if any(x in n.lower() for x in ('dataapi', 'subzero', 'database')):
            print(' ', n)

# 2) 控制面探测
sys_path = os.path.dirname(os.path.abspath(__file__))
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctx = ssl.create_default_context()

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, timeout=20)
    hdrs = {'Cookie': cookie_str(), 'Content-Type': 'application/json'}
    hdrs.update(HEADERS_TEST)
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

st, body = req('GET', API_BASE + '/projects?limit=50')
print('\n=== 项目列表 === raw status=%s' % st)
print(body[:600])
try:
    j = json.loads(body)
    for p in j.get('projects', []):
        print(' pid=%s name=%s region=%s pg_version=%s' % (p.get('id'), p.get('name'), p.get('region_id'), p.get('pg_version')))
except Exception as e:
    print('parse ERR:', e)
