# -*- coding: utf-8 -*-
"""会话诊断: users/me + / 重复请求, 判断 401 是会话过期还是请求问题"""
import http.client, ssl, re, os, sys, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST
m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)

def req(path, csrf=None, extra=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = csrf
        if extra:
            h.update(extra)
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw[:300]
    except Exception as e:
        return -1, 'EXC %s' % e

for i in range(3):
    st, b = req('/api/v2/users/me', CSRF)
    print('try%d users/me: %s %s' % (i, st, b), flush=True)
    time.sleep(1)
st, b = req('/')
print('GET /: %s %s' % (st, b[:200]), flush=True)
# 无 csrf 对比
st, b = req('/api/v2/users/me')
print('no-csrf users/me: %s %s' % (st, b), flush=True)
