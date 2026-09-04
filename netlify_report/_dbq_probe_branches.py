# -*- coding: utf-8 -*-
"""拿 A/B 的 database branches 结构"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    body = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, body


for name, tok, sid in [('A', TOKEN_A, SITE_A), ('B', TOKEN_B, SITE_B)]:
    st, b = api('GET', '/api/v1/sites/%s/database/branches' % sid, token=tok)
    print('%s_branches      [%d]' % (name, st))
    print(b[:2500])
    print()
