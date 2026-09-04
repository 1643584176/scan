# -*- coding: utf-8 -*-
"""Netlify:set-auth 假 token 测试"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

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
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return st, raw, hdrs

tests = [
    ('no auth', {}),
    ('fake token', {'Authorization': 'Bearer fake_token_12345'}),
    ('empty bearer', {'Authorization': 'Bearer '}),
    ('real token', {'Authorization': AUTH_HEADER}),
    ('access-control token 格式', {'Authorization': 'Bearer access-control-fake.eyJpdiI6IngifQ.abc'}),
    ('cookie only', {'Cookie': COOKIE_NET}),
]
for label, hdrs in tests:
    s, raw, hdrs_out = req('/access-control/set-auth', headers=hdrs)
    set_cookie = hdrs_out.get('set-cookie', '')
    print('%-28s %d body=%-40s set-cookie=%s' % (label, s,
          raw[:40].decode('utf-8', 'ignore').replace('\n', ' '), set_cookie[:60]))
