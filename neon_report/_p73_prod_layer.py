# -*- coding: utf-8 -*-
"""prod 认证面分层: /api/v2 401 是全局还是仅 API 网关?
测: 1. GET / 首页(HTML) 2. GET /auth/session/logout 3. /api/v2/users/me 对照
4. 带/不带 CSRF header 差异
"""
import http.client, ssl, json, sys, os, re

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF_RAW = m.group(1)

def req(path, csrf=None, cookie=True):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'text/html,application/json'}
        if cookie:
            h['Cookie'] = COOKIE_RAW
        if csrf:
            h['X-CSRF-Token'] = csrf
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        ct = dict(r.getheaders()).get('Content-Type', '')[:60]
        conn.close()
        return st, ct, raw[:260].decode('utf-8', 'ignore').replace('\n', ' ')
    except Exception as e:
        return -1, '', 'EXC %s' % e

tests = [
    ('GET / (cookie)', '/', None, True),
    ('GET /api/v2/users/me (cookie+csrf)', '/api/v2/users/me', CSRF_RAW, True),
    ('GET /api/v2/users/me (no cookie)', '/api/v2/users/me', None, False),
    ('GET /users/me (api/v2 无前缀)', '/users/me', None, True),
    ('GET /account (内部)', '/account', None, True),
    ('GET /ajax-api/test', '/ajax-api/2.0/test', None, True),
    ('GET /telemetry/v1 (bundle 里的 telemetry 域)', '/telemetry/v1', None, True),
]
for name, p, csrf, ck in tests:
    st, ct, body = req(p, csrf, ck)
    print('%-45s %s [%s] %s' % (name, st, ct, body[:180]), flush=True)
