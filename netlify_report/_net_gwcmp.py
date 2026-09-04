# -*- coding: utf-8 -*-
"""Netlify:bb-api 网关 vs api.netlify.com 直连 对比(匿名/认证)"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

ctx = ssl.create_default_context()

def req(host, path, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if headers:
        h.update(headers)
    conn.request('GET', path, headers=h)
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

paths = [
    '/api/v1/sites',
    '/api/v1/accounts',
    '/api/v1/accounts/1643584176',
    '/api/v1/1643584176/sites',
    '/api/v1/user',
    '/api/v1/sites/04f08ff6-f274-47ac-b6d7-5fb1e055f3b4',
]
print('%-40s %-8s %-8s %-8s %-8s' % ('path', 'api-anon', 'gw-anon', 'api-auth', 'gw-auth'))
for p in paths:
    sa, ba = req('api.netlify.com', p)
    sga, bga = req('app.netlify.com', '/access-control/bb-api' + p)
    sau, bau = req('api.netlify.com', p, headers={'Authorization': AUTH_HEADER})
    sgu, bgu = req('app.netlify.com', '/access-control/bb-api' + p, headers={'Cookie': COOKIE_NET})
    print('%-40s %-8s %-8s %-8s %-8s  %s' % (p, sa, sga, sau, sgu,
          bga[:60].decode('utf-8', 'ignore').replace('\n', ' ') if sga not in (200, 401) else ''))
