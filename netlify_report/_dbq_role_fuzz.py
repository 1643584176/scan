# -*- coding: utf-8 -*-
"""database-query role 参数探测:role 是否决定连接身份/是否有白名单
A site production,只读 SQL,观察 current_user 变化
"""
import http.client, ssl, gzip, brotli, json, time, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(role=None, branch='production'):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_A, 'branchId': branch, 'action': 'query',
            'sql': "select current_user::text as u, session_user::text as su"}
    if role is not None:
        body['role'] = role
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:600].decode('utf-8', 'ignore')
    conn.close()
    return st, out


for role in [None, 'readonly', 'netlifydb_owner', 'netlifydb_readonly', 'cloud_admin',
             'neon_superuser', 'postgres', 'owner', 'read', 'public', 'xxx', '"netlifydb_owner"']:
    st, out = q(role)
    print('role=%-20r [%d] %s' % (role, st, out[:200]))
