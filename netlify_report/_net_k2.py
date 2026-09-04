# -*- coding: utf-8 -*-
"""Netlify:spark-proxy knowledge 正确参数测试"""
import http.client, ssl, gzip, brotli, sys, json, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ACC_ID = '6a979dd2ae93f47d55b62897'
ctx = ssl.create_default_context()

def req(path, method='GET', body=None, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
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

tests = [
    ('GET', '/spark-proxy/api/v1/knowledge/?scopes=' + urllib.parse.quote(json.dumps({'siteId': SITE_ID, 'accountId': ACC_ID}))),
    ('GET', '/spark-proxy/api/v1/knowledge/?scopes=' + urllib.parse.quote(json.dumps({'siteId': SITE_ID}))),
    ('GET', '/spark-proxy/api/v1/knowledge/?scopes=' + urllib.parse.quote(json.dumps({'accountId': ACC_ID}))),
    ('GET', '/spark-proxy/api/v1/knowledge/?scopes=' + urllib.parse.quote(json.dumps({'siteId': SITE_ID, 'accountId': ACC_ID})) + '&ids=' + urllib.parse.quote(json.dumps(['general-context-for-agent-runners']))),
    ('POST', '/spark-proxy/api/v1/knowledge/', {'scopes': {'siteId': SITE_ID, 'accountId': ACC_ID}, 'id': 'general-context-for-agent-runners', 'type': 'general-context-for-agent-runners', 'data': {'test': 1}}),
]
for m, p, b in [(x[0], x[1], x[2] if len(x) > 2 else None) for x in tests]:
    try:
        s, raw = req(p, method=m, body=b, headers={'Cookie': COOKIE_NET})
        print('%-4s %-90s %d %s' % (m, p[:88], s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-4s %-90s ERR %s' % (m, p[:88], str(e)[:40]))
