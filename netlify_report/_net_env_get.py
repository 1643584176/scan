# -*- coding: utf-8 -*-
"""GET env 语义精确实验: site 路径 vs account 路径, 有无 context 参数, 写后 401 之谜"""
import http.client, ssl, gzip, brotli, json, sys, random
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

print('== A. B 站 GET 语义矩阵(T_C7263 应存在)==')
gets = [
    ('site env 无参',      '/api/v1/sites/%s/env' % SITE_B),
    ('site env ctx=prod', '/api/v1/sites/%s/env?context=production' % SITE_B),
    ('site env ctx=all',  '/api/v1/sites/%s/env?context=all' % SITE_B),
    ('acc env?site_id',   '/api/v1/accounts/%s/env?site_id=%s' % (ACC_B, SITE_B)),
    ('acc env 无 site',   '/api/v1/accounts/%s/env' % ACC_B),
    ('site env ?key',     '/api/v1/sites/%s/env?key=T_C7263' % SITE_B),
]
for tag, p in gets:
    st, b = req('GET', p, token=TOKEN_B)
    print('%-22s %s | %s' % (tag, st, b[:220]))

print()
print('== B. A 站写一个 env 再 GET(A 新体验对照)==')
KA = 'T_AX%s' % random.randint(1000, 9999)
st, b = req('POST', '/api/v1/accounts/' + ACC_A + '/env?site_id=' + SITE_A,
            [{'key': KA, 'values': [{'context': 'production', 'value': 'v'}]}], TOKEN_A)
print('A POST ->', st, b[:120])
for tag, p in [
    ('A site env 无参',   '/api/v1/sites/%s/env' % SITE_A),
    ('A acc env?site_id', '/api/v1/accounts/%s/env?site_id=%s' % (ACC_A, SITE_A)),
    ('A acc env 无 site', '/api/v1/accounts/%s/env' % ACC_A),
]:
    st, b = req('GET', p, token=TOKEN_A)
    print('%-22s %s | %s' % (tag, st, b[:220]))
print()
print('== C. 跨账号读 B 的 env(A token, 全路径)==')
for tag, p in [
    ('A读 B site env',  '/api/v1/sites/%s/env' % SITE_B),
    ('A读 B acc?site',  '/api/v1/accounts/%s/env?site_id=%s' % (ACC_B, SITE_B)),
]:
    st, b = req('GET', p, token=TOKEN_A)
    print('%-22s %s | %s' % (tag, st, b[:220]))

print()
print('== D. 清理: B 删 T_C7263, A 删 KA ==')
for k, acc, site, tok, tag in [
    ('T_C7263', ACC_B, SITE_B, TOKEN_B, 'B'),
    (KA, ACC_A, SITE_A, TOKEN_A, 'A'),
]:
    p = '/api/v1/accounts/%s/env/%s?site_id=%s' % (acc, k, site)
    st, b = req('DELETE', p, token=tok)
    print('%-8s DEL %s | %s' % (tag, st, b[:80]))
    st, b = req('GET', '/api/v1/sites/%s/env' % site, token=tok)
    print('%-8s GET after del | %s | %s' % (tag, st, b[:150]))
print('done')
