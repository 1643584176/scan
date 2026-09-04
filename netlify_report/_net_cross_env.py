# -*- coding: utf-8 -*-
"""Netlify 跨账号 env vars / log drains / database API 交叉测试
规则内:多账号测试自己资源"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def api(token, path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    payload = None
    if body is not None:
        h['Content-Type'] = 'application/json'
        payload = json.dumps(body).encode()
    try:
        conn.request(method, path, body=payload, headers=h)
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st = r.status
        conn.close()
        return st, raw[:400]
    except Exception as e:
        return 'ERR', str(e)[:80].encode()

# 0. 两个账号自己的 account id
for name, tk in (('A', TOKEN_A), ('B', TOKEN_B)):
    st, raw = api(tk, '/api/v1/accounts')
    print('[%s] accounts %s %s' % (name, st, raw[:300].decode('utf-8', 'replace')))
print()

# 交叉测试(用对方 token 访问自己的资源 = 越权探测)
cross = [
    # (label, token, method, path, body)
    ('B->A account env',      TOKEN_B, 'GET',  '/api/v1/accounts/1643584176/env', None),
    ('B->A site env',         TOKEN_B, 'GET',  '/api/v1/sites/%s/env' % SITE_A, None),
    ('B->A site env key X',   TOKEN_B, 'GET',  '/api/v1/sites/%s/env/ZZZ_NOPE' % SITE_A, None),
    ('B->A db owner',         TOKEN_B, 'GET',  '/api/v1/sites/%s/database?role=netlifydb_owner' % SITE_A, None),
    ('A->B site env',         TOKEN_A, 'GET',  '/api/v1/sites/%s/env' % SITE_B, None),
    ('A->B account env',      TOKEN_A, 'GET',  '/api/v1/accounts/libobo01/env', None),
    ('A->B db readonly',      TOKEN_A, 'GET',  '/api/v1/sites/%s/database?role=readonly' % SITE_B, None),
    # log drains 端点是否存在(OpenAPI 外)
    ('B->A log-drains',       TOKEN_B, 'GET',  '/api/v1/sites/%s/log-drains' % SITE_A, None),
    ('A->B log-drains',       TOKEN_A, 'GET',  '/api/v1/sites/%s/log-drains' % SITE_B, None),
    ('B->A audit',            TOKEN_B, 'GET',  '/api/v1/accounts/1643584176/audit?log_type=all', None),
    ('A->B metadata',         TOKEN_A, 'GET',  '/api/v1/sites/%s/metadata' % SITE_B, None),
    ('B->A metadata',         TOKEN_B, 'GET',  '/api/v1/sites/%s/metadata' % SITE_A, None),
]
for label, tk, m, p, b in cross:
    st, raw = api(tk, p, m, b)
    print('%-22s %s %s' % (label, st, raw.decode('utf-8', 'replace')[:250].replace('\n', ' ')))
