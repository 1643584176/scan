# -*- coding: utf-8 -*-
"""Netlify:spark-proxy JSON scopes + 网关认证变体"""
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

import urllib.parse
# spark-proxy knowledge 正确格式
for scopes in [["site"], ["global"], ["site", "global"], ["account"], ["team"], ["user"]]:
    q = 'scopes=' + urllib.parse.quote(json.dumps(scopes))
    p = '/spark-proxy/api/v1/knowledge/?' + q
    s, raw = req('app.netlify.com', p, headers={'Cookie': COOKIE_NET})
    print('knowledge %-22s %d %s' % (scopes, s, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')))

print()
# 网关认证变体
for hdrs in [{'Authorization': AUTH_HEADER}, {'Authorization': AUTH_HEADER, 'Cookie': COOKIE_NET},
             {'Cookie': COOKIE_NET}, {'X-Forwarded-For': '127.0.0.1'}]:
    s, raw = req('app.netlify.com', '/access-control/bb-api/api/v1/user', headers=hdrs)
    print('gw auth %-60s %d %s' % (str(hdrs)[:58], s, raw[:60].decode('utf-8', 'ignore').replace('\n', ' ')))

# 网关 openapi 文档看看有没有隐藏端点
s, raw = req('app.netlify.com', '/access-control/bb-api/api/v1', headers={'Cookie': COOKIE_NET})
print()
print('gw /api/v1:', s, raw[:400].decode('utf-8', 'ignore'))
