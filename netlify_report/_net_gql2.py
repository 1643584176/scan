# -*- coding: utf-8 -*-
"""Netlify:探测 GraphQL 端点"""
import http.client, ssl, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

ctx = ssl.create_default_context()

def req(host, path, method='GET', body=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': '*/*'}
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
        import brotli
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        import gzip
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

ql = '{"query":"{__typename}"}'
targets = [
    ('api.netlify.com', '/graphql'),
    ('api.netlify.com', '/api/graphql'),
    ('api.netlify.com', '/v1/graphql'),
    ('app.netlify.com', '/graphql'),
    ('app.netlify.com', '/api/graphql'),
    ('graphql.netlify.com', '/'),
    ('graphql.netlify.com', '/graphql'),
    ('apps.netlify.com', '/graphql'),
    ('connect.netlify.com', '/graphql'),
    ('data.netlify.com', '/graphql'),
]
for host, p in targets:
    try:
        # 匿名 GET
        s1, raw1 = req(host, p)
        # 匿名 POST introspection
        s2, raw2 = req(host, p, method='POST', body=ql)
        b2 = raw2[:90].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-22s %-14s GET=%d POST=%d %s' % (host, p, s1, s2, b2))
    except Exception as e:
        print('%-22s %-14s ERR %s' % (host, p, str(e)[:40]))
