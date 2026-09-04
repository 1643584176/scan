# -*- coding: utf-8 -*-
"""Netlify:featureflags.netlify.com 探测"""
import http.client, ssl, gzip, brotli, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

ctx = ssl.create_default_context()

def req(host, path, method='GET', headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': '*/*'}
    if headers:
        h.update(headers)
    conn.request(method, path, headers=h)
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

for path in ['/', '/flags', '/api/flags', '/api/v1/flags', '/v1/flags', '/feature-flags',
             '/api/feature-flags', '/flags.json', '/api/flags.json', '/health', '/status',
             '/.netlify/functions/flags', '/debug', '/internal/flags']:
    try:
        s, raw, hdrs = req('featureflags.netlify.com', path)
        loc = hdrs.get('location', '')
        print('%-30s %d loc=%-40s ct=%-25s %s' % (path, s, loc[:40], hdrs.get('content-type', '')[:25],
              raw[:60].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-30s ERR %s' % (path, str(e)[:40]))

# 跟 308 跳转(带 cookie)
print()
s, raw, hdrs = req('featureflags.netlify.com', '/', headers={'Cookie': COOKIE_NET})
print('with cookie:', s, hdrs.get('location'))
