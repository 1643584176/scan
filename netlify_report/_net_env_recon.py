# -*- coding: utf-8 -*-
"""env API 侦察: A/B 站点的 env REST 路径形态探测"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=20):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

paths = [
    '/api/v1/sites/%s/env',
    '/api/v1/sites/%s/env?context=production',
    '/api/v1/sites/%s/env/all',
    '/api/v1/sites/%s/environment',
    '/api/v1/sites/%s/environment-variables',
    '/api/v1/env?site_id=%s',
    '/api/v1/accounts/6a979dd2ae93f47d55b62897/env?site_id=%s',
]
for site, tok, tag in [(SITE_A, TOKEN_A, 'A'), (SITE_B, TOKEN_B, 'B')]:
    print('==== site', tag, site, '====')
    for p in paths:
        st, b = req('GET', p % site, token=tok)
        print('%-55s %s | %s' % (p % '<id>', st, b[:160].replace('\n', ' ')))
    print()
