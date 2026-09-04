# -*- coding: utf-8 -*-
"""branch 对照:B cookie 访问自己的 agent 分支(验证分支有效)+ A cookie 交叉(预期 404)"""
import http.client, ssl, gzip, brotli, json, time, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
BRANCH_B = 'agent-6a98d5e6448c07a76d7babf3'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(site_id, branch_id, cookie):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': cookie,
         'Content-Type': 'application/json'}
    body = {'siteId': site_id, 'branchId': branch_id, 'action': 'query',
            'sql': "select current_user::text as u, current_database()::text as db, inet_server_addr()::text as srv"}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:1000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


cases = [
    ('B_cookie+B_site+B_branch', COOKIE_B, SITE_B, BRANCH_B),
    ('A_cookie+B_site+B_branch', COOKIE_A, SITE_B, BRANCH_B),
    ('B_cookie+A_site+A_prod  ', COOKIE_B, '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', 'production'),
]
for name, ck, sid, bid in cases:
    st, out = q(sid, bid, ck)
    print('%-24s [%d]' % (name, st))
    print('   ' + out[:600])
    print()
