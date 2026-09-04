# -*- coding: utf-8 -*-
"""role=Admin + site_access 组合邀请 B, 成功后找接受路径"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
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

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-60s %s | %s' % (tag, st, b[:300].replace('\n', ' ')))
    return st, b

print('== 1. Admin 邀请(site_access 各种值) ==')
for sa in ['all', SITE_A, [SITE_A]]:
    st, b = probe('POST members role=Admin sa=%s' % sa, 'POST',
                  '/api/v1/1643584176/members',
                  {'email': '729488839@qq.com', 'role': 'Admin', 'site_access': sa})
    if st in (200, 201, 202):
        print('    SUCCESS!')
        invite = b
        break
else:
    invite = None
    print('    (无成功组合)')

if invite:
    print()
    print('== 2. B 视角: 找待接受邀请 ==')
    st, b = probe('B GET /invites', 'GET', '/api/v1/invites', None, TOKEN_B)
    st, b = probe('B GET /user/invites', 'GET', '/api/v1/user/invites', None, TOKEN_B)
    st, b = probe('B GET /1643584176/invites', 'GET', '/api/v1/1643584176/invites', None, TOKEN_B)
    st, b = probe('B GET accounts(invites 字段?)', 'GET', '/api/v1/accounts', None, TOKEN_B)
    print()
    print('invite body from step1:', invite[:800])
print('done')
