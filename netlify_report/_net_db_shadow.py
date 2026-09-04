# -*- coding: utf-8 -*-
"""database 影子方法(POST/DELETE)探测: 先跨账号(无风险), 再本体形态"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=25):
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

def probe(tag, m, p, body=None, tok=None):
    st, b = req(m, p, body, tok)
    print('%-46s %s | %s' % (tag, st, b[:200].replace('\n', ' ')))
    return st, b

print('== 1. 跨账号(无风险优先)==')
probe('B DELETE A database', 'DELETE', '/api/v1/sites/%s/database' % SITE_A, None, TOKEN_B)
probe('B POST A database 空', 'POST', '/api/v1/sites/%s/database' % SITE_A, {}, TOKEN_B)
probe('B DELETE B 自己 database', 'DELETE', '/api/v1/sites/%s/database' % SITE_B, None, TOKEN_B)

print()
print('== 2. A 本体形态(空 body 看错误)==')
probe('A POST 空 body', 'POST', '/api/v1/sites/%s/database' % SITE_A, {}, TOKEN_A)
probe('A DELETE 空', 'DELETE', '/api/v1/sites/%s/database' % SITE_A, None, TOKEN_A)
print('done')
