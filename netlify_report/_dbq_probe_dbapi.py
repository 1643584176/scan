# -*- coding: utf-8 -*-
"""侦察 database API:拿 A/B site 的 database 对象完整结构(branch/branchId/connection)"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

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


# A 的 database
st, b = api('GET', '/api/v1/sites/%s/database' % SITE_A, token=TOKEN_A)
print('A_db              [%d]' % st)
print(b[:3000])
print()
