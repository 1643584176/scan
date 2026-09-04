# -*- coding: utf-8 -*-
"""查控制面 org 列表(真实 org id 格式)"""
import http.client, ssl, json, re, html, sys, os, urllib.parse

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def csrf_cookie(cookie):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie.split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    return '; '.join(parts), csrf

def ctl(method, path, body=None):
    ck, csrf = csrf_cookie(cookie_str())
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    hdrs = {'Cookie': ck, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf,
            'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    raw = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, raw

for path in ['/organizations', '/users/me/organizations', '/organizations?limit=20']:
    st, raw = ctl('GET', path)
    print('GET %s -> %d %s' % (path, st, raw[:600].replace('\n', ' ')), flush=True)
