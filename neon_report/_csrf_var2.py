# -*- coding: utf-8 -*-
"""变体:带 cookie GET 首页/API 看是否刷新 csrf;并 grep 首页 HTML 的 csrf 注入点"""
import http.client, ssl, re, sys, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE

ctx = ssl.create_default_context()

def get_with_cookie(path):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse(); body = r.read()
    sc = r.headers.get_all('Set-Cookie') or []
    conn.close()
    return r.status, body, sc

# 1. 带 cookie GET 首页
st, body, sc = get_with_cookie('/')
print('GET / with cookie:', st, 'set-cookie:', len(sc))
for s in sc:
    if '_gorilla_csrf' in s or 'keycloak' in s.lower():
        print('  SC:', s[:100])

# 2. 带 cookie GET api/v2/auth
st, body, sc = get_with_cookie(API_BASE + '/auth')
print('GET /api/v2/auth with cookie:', st, 'set-cookie:', len(sc))
for s in sc:
    if '_gorilla_csrf' in s:
        print('  SC:', s[:100])

# 3. 首页 HTML 里找 csrf 注入(meta/JS 变量)
st, body, sc = get_with_cookie('/')
txt = body.decode('utf-8', 'replace')
hits = [m.start() for m in re.finditer('csrf|CSRF', txt)][:10]
print('html csrf hits:', len(hits))
for i in hits[:5]:
    print('  CTX:', txt[max(0, i - 100):i + 150].replace('\n', ' ')[:250])
