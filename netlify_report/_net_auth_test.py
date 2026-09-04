# -*- coding: utf-8 -*-
"""Netlify:测试 app 域 cookie 生效面 + access-control 网关"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

ctx = ssl.create_default_context()

def req(host, path, method='GET', headers=None, body=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET}
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

print('=== app.netlify.com cookie 生效面 ===')
for p in ['/access-control/generate-access-control-token',
          '/access-control/create-api',
          '/access-control/set-auth',
          '/access-control/bb-api',
          '/access-control/analytics-api']:
    try:
        s, raw, hdrs = req('app.netlify.com', p)
        print('%-48s %d %s' % (p, s, raw[:180].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-48s ERR %s' % (p, str(e)[:50]))

print()
print('=== api.netlify.com 带 Authorization 变体 ===')
for ah in ['Bearer nfu_L83buRGvkmnPGcZNX5gp9C9Bt9J9BwGf4678',
           'nfu_L83buRGvkmnPGcZNX5gp9C9Bt9J9BwGf4678',
           'Bearer znEEUoPL_WBYuyKiOoBXqvt9awROSg_y']:
    s, raw, hdrs = req('api.netlify.com', '/api/v1/user', headers={'Authorization': ah})
    print('Auth=%-50s -> %d %s' % (ah[:48], s, raw[:80].decode('utf-8', 'ignore')))
