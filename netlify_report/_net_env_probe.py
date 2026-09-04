# -*- coding: utf-8 -*-
"""env API 写入形态探测(B 站): POST body 结构学习 + account env 查询语义
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ACC_A = '6a979dd2ae93f47d55b62897'
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

print('== 1. POST /api/v1/sites/B/env body 结构学习 ==')
bodies = [
    {'key': 'T_E1', 'value': 'v1', 'context': 'production'},
    {'key': 'T_E1', 'values': [{'context': 'production', 'value': 'v1'}]},
    {},
    {'key': 'T_E1', 'value': 'v1'},
]
for bd in bodies:
    st, b = req('POST', '/api/v1/sites/' + SITE_B + '/env', bd, TOKEN_B)
    print('body %-70s -> %s | %s' % (json.dumps(bd)[:68], st, b[:200].replace('\n', ' ')))

print()
print('== 2. account env 查询语义(空 body 阶段) ==')
for p, tok in [
    ('/api/v1/accounts/' + ACC_A + '/env', TOKEN_A),
    ('/api/v1/accounts/' + ACC_A + '/env?site_id=' + SITE_B, TOKEN_A),
]:
    st, b = req('GET', p, token=tok)
    print('%-70s -> %s | %s' % (p, st, b[:200]))
print('done')
