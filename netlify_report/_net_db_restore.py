# -*- coding: utf-8 -*-
"""恢复被 DELETE 的 database: POST 语义确认 + GET 状态"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=30):
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

print('== 1. 删除后状态 ==')
for tag, site, tok in [('A', SITE_A, TOKEN_A), ('B', SITE_B, TOKEN_B)]:
    st, b = req('GET', '/api/v1/sites/%s/database' % site, token=tok)
    print('%s GET after del: %s | %s' % (tag, st, b[:150]))
    st, b = req('GET', '/api/v1/sites/%s/database/branches' % site, token=tok)
    print('%s branches: %s | %s' % (tag, st, b[:150]))

print()
print('== 2. POST 尝试重建 ==')
for tag, site, tok in [('A', SITE_A, TOKEN_A), ('B', SITE_B, TOKEN_B)]:
    st, b = req('POST', '/api/v1/sites/%s/database' % site, {}, tok)
    print('%s POST: %s | %s' % (tag, st, b[:300]))
    time.sleep(2)
    st, b = req('GET', '/api/v1/sites/%s/database' % site, token=tok)
    print('%s GET after POST: %s | %s' % (tag, st, b[:150]))
print('done')
