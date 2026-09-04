# -*- coding: utf-8 -*-
"""CSRF 握手:无 cookie GET 首页 -> 收集 Set-Cookie 新 csrf -> 用它 POST"""
import http.client, ssl, json, sys, urllib.parse, re
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

# 1. 无 cookie GET 首页,收集 Set-Cookie
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse(); body = r.read()
set_cookies = r.headers.get_all('Set-Cookie') or []
conn.close()
print('GET / status:', r.status, 'set-cookie count:', len(set_cookies))
new_csrf = None
for sc in set_cookies:
    m = re.match(r'_gorilla_csrf=([^;]+)', sc)
    if m:
        new_csrf = m.group(1)
        print('new _gorilla_csrf len:', len(new_csrf))
        break

if not new_csrf:
    print('no new csrf cookie'); sys.exit(1)

# 2. 组合 cookie:新 csrf + 旧会话(去旧 csrf)
parts = []
for c in cookie_str().split(';'):
    c = c.strip()
    if c.startswith('_gorilla_csrf='):
        continue
    parts.append(c)
merged = '_gorilla_csrf=' + new_csrf + '; ' + '; '.join(parts)

def post(label, csrf_hdr):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': merged, 'X-Bug-Bounty': 'xxbo'}
    if csrf_hdr:
        h['X-CSRF-Token'] = csrf_hdr
    conn.request('POST', API_BASE + '/projects?org_id=%s' % ORG,
                 body=json.dumps({'project': {'name': 'sec-hs-1'}}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    print('%-22s -> %d %s' % (label, st, raw[:220]))

post('new csrf raw', new_csrf)
post('new csrf unquote', urllib.parse.unquote(new_csrf))
