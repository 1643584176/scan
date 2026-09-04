# -*- coding: utf-8 -*-
"""Netlify:accessControlToken 用途 + /api/* HTML 响应 + labs"""
import http.client, ssl, gzip, brotli, json, sys, base64
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

ctx = ssl.create_default_context()

def req(host, path, method='GET', headers=None, body=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
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

# 1. 获取 accessControlToken 并解析 JWT
s, raw, hdrs = req('app.netlify.com', '/access-control/generate-access-control-token', headers={'Cookie': COOKIE_NET})
print('generate-access-control-token:', s)
tok = None
try:
    d = json.loads(raw)
    tok = d.get('accessControlToken')
    print('  token prefix:', tok[:40] if tok else None)
    if tok:
        # JWT payload(base64url)
        parts = tok.split('.')
        if len(parts) >= 2:
            pad = parts[1] + '=' * (-len(parts[1]) % 4)
            print('  payload:', base64.urlsafe_b64decode(pad)[:300].decode('utf-8', 'ignore'))
except Exception as e:
    print('  parse err', e, raw[:150].decode('utf-8', 'ignore'))

# 2. accessControlToken 能否调 api.netlify.com
if tok:
    for hdr_name in ['Authorization', 'X-Access-Control-Token', 'Access-Control-Token']:
        s2, raw2, h2 = req('api.netlify.com', '/api/v1/user', headers={hdr_name: 'Bearer ' + tok})
        print('api user with %s: %d %s' % (hdr_name, s2, raw2[:80].decode('utf-8', 'ignore')))
        s2b, raw2b, h2b = req('api.netlify.com', '/api/v1/user', headers={hdr_name: tok})
        print('api user with %s(raw): %d %s' % (hdr_name, s2b, raw2b[:80].decode('utf-8', 'ignore')))

# 3. /api/* HTML 响应是什么
for p in ['/api/experiments', '/api/deploy-diagnostics', '/api/agent-runners/status']:
    s, raw, hdrs = req('app.netlify.com', p)
    ct = hdrs.get('content-type', '')
    print('/%s -> %d ct=%s len=%d' % (p, s, ct, len(raw)))
    if 'html' in ct:
        txt = raw.decode('utf-8', 'ignore')
        i = txt.find('<title>')
        print('   title:', txt[i:i + 80] if i >= 0 else '?')

# 4. labs-list 带 cookie
s, raw, hdrs = req('app.netlify.com', '/.netlify/functions/labs-list', headers={'Cookie': COOKIE_NET})
print('labs-list auth:', s, raw[:300].decode('utf-8', 'ignore'))
