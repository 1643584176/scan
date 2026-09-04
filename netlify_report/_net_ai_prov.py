# -*- coding: utf-8 -*-
"""深挖: ai-gateway/providers 完整 + accounts/types + 鉴权(匿名/B) + audit 跨账号 + 清理残留"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
ACC_A = '6a979dd2ae93f47d55b62897'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
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
    print('%-56s %s | %s' % (tag, st, b[:400].replace('\n', ' ')))
    return st, b

print('== 1. ai-gateway/providers 完整(A / 匿名 / B) ==')
st, b = probe('A GET providers', 'GET', '/api/v1/ai-gateway/providers')
st, b = probe('匿名 GET providers', 'GET', '/api/v1/ai-gateway/providers', None, None)
st, b = probe('B GET providers', 'GET', '/api/v1/ai-gateway/providers', None, TOKEN_B)
print()
print('== 2. accounts/types 匿名可读? ==')
st, b = probe('匿名 GET accounts/types', 'GET', '/api/v1/accounts/types', None, None)
print()
print('== 3. audit 跨账号 ==')
st, b = probe('A GET 自己 audit', 'GET', '/api/v1/accounts/%s/audit' % ACC_A)
st, b = probe('B GET A audit', 'GET', '/api/v1/accounts/%s/audit' % ACC_A, None, TOKEN_B)
st, b = probe('匿名 GET A audit', 'GET', '/api/v1/accounts/%s/audit' % ACC_A, None, None)
print()
print('== 4. 遗留站点与 zone 清理 ==')
st, b = probe('DELETE zz2 zone', 'DELETE', '/api/v1/dns_zones/6a97ed148d21ff008fcd8843')
st, b = probe('DELETE sec-a-nod 遗留站点', 'DELETE', '/api/v1/sites/25234194-9aab-4961-842d-427b50754dcc')
print('done')
