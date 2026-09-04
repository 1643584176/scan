# -*- coding: utf-8 -*-
"""越权矩阵:GET /api/v1/sites/{site}/database 跨账号访问
A-token x A-site / A-token x B-site / B-token x B-site / B-token x A-site
"""
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


def mask(conn_str):
    """连接串打码:只留 host"""
    import re
    m = re.match(r'(postgresql://[^:]+:)([^@]+)(@[^/]+/.+)', conn_str or '')
    return '%s***%s' % (m.group(1), m.group(3)) if m else conn_str


cases = [
    ('A->A', TOKEN_A, SITE_A),
    ('A->B', TOKEN_A, SITE_B),
    ('B->B', TOKEN_B, SITE_B),
    ('B->A', TOKEN_B, SITE_A),
]
for name, tok, sid in cases:
    st, b = api('GET', '/api/v1/sites/%s/database' % sid, token=tok)
    print('%-6s GET /database [%d]' % (name, st))
    if st == 200:
        try:
            j = json.loads(b)
            cs = j.get('connection_string') or ''
            print('   owner cs : %s' % mask(cs))
            print('   branches : %s' % [k for k in j.keys()])
        except Exception:
            print('   body:', b[:400])
    else:
        print('   body:', b[:200])
    print()
