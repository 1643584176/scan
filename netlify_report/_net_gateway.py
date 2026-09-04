# -*- coding: utf-8 -*-
"""Netlify:/access-control/ 网关子路径探测 + 公开 siteId 渠道"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

ctx = ssl.create_default_context()

def req(path, method='GET', headers=None, body=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
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

# bb-api 子路径猜测(buildbot api)
paths = [
    '/access-control/bb-api/v1/builds',
    '/access-control/bb-api/api/v1/builds',
    '/access-control/bb-api/',
    '/access-control/bb-api/health',
    '/access-control/bb-api/v1/sites',
    '/access-control/analytics-api/',
    '/access-control/analytics-api/v1/analytics',
    '/access-control/analytics-api/graphql',
    '/access-control/analytics-api/query',
    '/access-control/create-api/',
    '/access-control/create-api/sites',
    '/access-control/set-auth/',
    '/access-control/set-auth/token',
    '/access-control/',
    '/access-control/generate-access-control-token/',
]
print('--- anon ---')
for p in paths:
    try:
        s, raw = req(p)
        print('%-58s %d %s' % (p, s, raw[:70].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-58s ERR' % p)
print('--- auth(cookie) ---')
for p in paths:
    try:
        s, raw = req(p, headers={'Cookie': COOKIE_NET})
        print('%-58s %d %s' % (p, s, raw[:70].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-58s ERR' % p)
