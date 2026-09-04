# -*- coding: utf-8 -*-
"""Netlify:database connection-string 权限矩阵(带 role 参数精确测)"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

def api(path, token=TOKEN_A, method='GET', qs=''):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    conn.request(method, path + qs, headers=h)
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
    ('A GET own db      ', SITE_A, TOKEN_A, ''),
    ('A GET own db role ', SITE_A, TOKEN_A, '?role=netlifydb_owner'),
    ('A GET own ro role ', SITE_A, TOKEN_A, '?role=netlifydb_readonly'),
    ('A GET B db role   ', SITE_B, TOKEN_A, '?role=netlifydb_owner'),
    ('A GET B ro role   ', SITE_B, TOKEN_A, '?role=netlifydb_readonly'),
    ('A GET B branches  ', SITE_B, TOKEN_A, '/branches'),
    ('A GET B db noconn ', SITE_B, TOKEN_A, '?role=nonexistent'),
]
for label, sid, tok, qs in tests:
    p = '/api/v1/sites/%s/database' % sid
    st, raw = api(p, tok, qs=qs)
    txt = raw.decode('utf-8', 'ignore').replace('\n', ' ')
    print('%-22s %d %s' % (label, st, txt[:130]))
