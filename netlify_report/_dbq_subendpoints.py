# -*- coding: utf-8 -*-
"""database REST 子端点摸底(GET 只读):settings/compute/snapshots/time_series 等
每个端点:自己 site(200?) + 交叉 B site(401?)"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept': 'application/json'}
    h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


subs = ['settings', 'compute', 'snapshots', 'snapshot', 'deploy-and-rollback',
        'time_series', 'time-series', 'branch', 'branches/production']
for sub in subs:
    st, out = api('GET', '/api/v1/sites/%s/database/%s' % (SITE_A, sub), TOKEN_A)
    tag = 'SELF'
    if st == 401 or st == 403:
        # 可能是子路径不存在而非越权;交叉测 B site 对照(应该都是 401 Access Denied 如果鉴权前置)
        stb, outb = api('GET', '/api/v1/sites/%s/database/%s' % (SITE_B, sub), TOKEN_A)
        print('%-20s A:[%d] B(A-tok):[%d] %s' % (sub, st, stb, out[:150].replace('\n', ' ')))
    else:
        print('%-20s A:[%d] %s' % (sub, st, out[:250].replace('\n', ' ')))
