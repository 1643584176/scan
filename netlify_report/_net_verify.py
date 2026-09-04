# -*- coding: utf-8 -*-
"""Netlify:验证 cookie + 获取账号基线"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

ctx = ssl.create_default_context()

def get(host, path, headers=None, method='GET', body=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json',
         'Cookie': COOKIE_NET}
    if headers:
        h.update(headers)
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return st, raw, hdrs

# 1. user
s, raw, hdrs = get('api.netlify.com', '/api/v1/user')
print('GET /api/v1/user:', s)
if s == 200:
    try:
        u = json.loads(raw)
        for k in ['id', 'email', 'full_name', 'avatar_url', 'created_at', 'uid']:
            if k in u:
                print('  %s: %s' % (k, str(u[k])[:100]))
    except Exception as e:
        print('  parse err', e, raw[:200])
else:
    print('  body:', raw[:200].decode('utf-8', 'ignore'))

# 2. accounts
s, raw, hdrs = get('api.netlify.com', '/api/v1/accounts')
print('GET /api/v1/accounts:', s)
if s == 200:
    try:
        accs = json.loads(raw)
        for a in accs:
            print('  account: id=%s slug=%s name=%s type=%s role=%s' % (
                a.get('id'), a.get('slug'), a.get('name'), a.get('type'), a.get('roles_allowed')))
    except Exception as e:
        print('  parse err', e, raw[:200])
else:
    print('  body:', raw[:200].decode('utf-8', 'ignore'))

# 3. 团队成员
s, raw, hdrs = get('api.netlify.com', '/api/v1/%s/members' % '1643584176')
print('GET /{account_slug}/members:', s)
if s == 200:
    try:
        ms = json.loads(raw)
        for m in ms[:5]:
            print('  member: id=%s email=%s role=%s' % (m.get('id'), m.get('email'), m.get('role')))
    except Exception as e:
        print('  parse err', e, raw[:200])
else:
    print('  body:', raw[:200].decode('utf-8', 'ignore'))
