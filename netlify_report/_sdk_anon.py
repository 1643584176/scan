# -*- coding: utf-8 -*-
"""sdk-version 匿名可达性测试"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

ctx = ssl.create_default_context()

def post(cookie=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
    h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    conn.request('POST', '/.netlify/functions/fetch-extension-host-site-sdk-version',
                 body=json.dumps({'siteUrl': 'https://example.com'}).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read(300)
    st = r.status
    conn.close()
    return st, raw

st, raw = post()
print('anonymous:', st, raw[:150].decode('utf-8', 'replace'))
st2, raw2 = post(COOKIE_B)
print('with cookie B:', st2, raw2[:150].decode('utf-8', 'replace'))
