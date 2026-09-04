# -*- coding: utf-8 -*-
"""env 写 API 探测(旧 PUT query 风格)+ account env 校验矩阵"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

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

print('== 1. 写 API 形态(B 站旧体验?) ==')
writes = [
    ('PUT', '/api/v1/sites/' + SITE_B + '/env?key=T_E1&value=v1&context=production'),
    ('PUT', '/api/v1/sites/' + SITE_B + '/env'),
    ('PATCH', '/api/v1/sites/' + SITE_B + '/env/T_E1'),
    ('PUT', '/api/v1/sites/' + SITE_B + '/env/T_E1'),
    ('POST', '/api/v1/accounts/' + ACC_B + '/env?site_id=' + SITE_B),
    ('PUT', '/api/v1/accounts/' + ACC_B + '/env?site_id=' + SITE_B),
]
for m, p in writes:
    st, b = req(m, p, {'key': 'T_E1', 'value': 'v1', 'context': 'production'} if m in ('PATCH', 'POST') else None,
                TOKEN_B)
    print('%-7s %-80s -> %s | %s' % (m, p, st, b[:120]))

print()
print('== 2. GET env 现状 ==')
for p, tok, tag in [
    ('/api/v1/sites/' + SITE_B + '/env', TOKEN_B, 'B own'),
    ('/api/v1/sites/' + SITE_A + '/env', TOKEN_A, 'A own'),
]:
    st, b = req('GET', p, token=tok)
    print('%-20s %s | %s' % (tag, st, b[:200]))

print()
print('== 3. account env 校验矩阵(GET)==')
matrix = [
    ('A tok accA siteA', TOKEN_A, ACC_A, SITE_A),
    ('A tok accA siteB', TOKEN_A, ACC_A, SITE_B),
    ('A tok accB siteB', TOKEN_A, ACC_B, SITE_B),
    ('B tok accA siteB', TOKEN_B, ACC_A, SITE_B),
    ('B tok accB siteA', TOKEN_B, ACC_B, SITE_A),
    ('B tok accA siteA', TOKEN_B, ACC_A, SITE_A),
    ('B tok accB siteB', TOKEN_B, ACC_B, SITE_B),
]
for tag, tok, acc, site in matrix:
    p = '/api/v1/accounts/%s/env?site_id=%s' % (acc, site)
    st, b = req('GET', p, token=tok)
    print('%-22s -> %s | %s' % (tag, st, b[:100]))
print('done')
