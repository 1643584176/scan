# -*- coding: utf-8 -*-
"""新鲜 cookie 验证 + database_instances 端点探测(零破坏只读):
1. 会话: GET / -> 200? GET /api/v2/users/me
2. database_instances 列表 + 相关端点分层
"""
import http.client, ssl, json, sys, os, re, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)

def req(path, csrf=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = csrf
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw[:600].replace('\n', ' ')
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== 1. 会话验证 ===', flush=True)
for p in ['/', '/api/v2/users/me', '/api/v2/projects?limit=5', '/api/v2/organizations']:
    st, body = req(p, CSRF)
    print('%-35s %s %s' % (p, st, body[:250]), flush=True)
    time.sleep(0.3)

print('=== 2. database_instances ===', flush=True)
for p in ['/api/v2/database_instances',
          '/api/v2/database_instances?page_size=10',
          '/api/v2/database-instances']:
    st, body = req(p, CSRF)
    print('%-45s %s %s' % (p, st, body[:400]), flush=True)
    time.sleep(0.3)
