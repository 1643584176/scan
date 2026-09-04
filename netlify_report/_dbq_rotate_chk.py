# -*- coding: utf-8 -*-
"""rotate_credentials 鉴权矩阵(只发非法/不存在对象,不真旋转有效凭据)
A-token x A-site(不存在 branch,验证 branch 校验)
A-token x B-site(越权,预期 401)
"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token=None, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


cases = [
    # 不存在 branch:测校验顺序,不碰真实凭据
    ('A_site+bad_branch', '/api/v1/sites/%s/database/rotate_credentials' % SITE_A,
     {'rotations': [{'branch': 'no-such-branch-xyz', 'roles': ['netlifydb_owner']}]}),
    # 越权:site 不属 A
    ('A_token+B_site   ', '/api/v1/sites/%s/database/rotate_credentials' % SITE_B,
     {'rotations': [{'branch': 'production', 'roles': ['netlifydb_owner']}]}),
    # 空 roles
    ('A_site+empty     ', '/api/v1/sites/%s/database/rotate_credentials' % SITE_A,
     {'rotations': [{'branch': 'production', 'roles': []}]}),
]
for name, path, body in cases:
    st, out = api('POST', path, token=TOKEN_A, body=body)
    print('%-20s [%d] %s' % (name, st, out[:300]))
