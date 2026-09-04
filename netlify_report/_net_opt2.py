# -*- coding: utf-8 -*-
"""OPTIONS 原始响应抽查 + 全 path 不筛选输出"""
import http.client, ssl, gzip, brotli, json, sys, re
import yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def req(method, path, token=None, timeout=15):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    allow = r.getheader('Allow', '')
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, allow, txt

print('== 抽查 ==')
for p in ['/api/v1/user', '/api/v1/sites/' + SITE_A, '/api/v1/sites/' + SITE_A + '/deploys',
          '/api/v1/accounts', '/api/v1/purge']:
    st, a, b = req('OPTIONS', p, TOKEN_A)
    print('OPTIONS %-45s %s allow=%s | %s' % (p, st, a or '-', b[:60]))

print()
print('== 全 path OPTIONS ==')
with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)
paths = spec['paths']
cnt = 0
for p in sorted(paths.keys()):
    pp = ('/api/v1' + p) if not p.startswith('/api/v1') else p
    pp = pp.replace('{site_id}', SITE_A).replace('{account_id}', '6a979dd2ae93f47d55b62897')
    pp = re.sub(r'\{[^}]+\}', 'zz-fake-0001', pp)
    st, a, b = req('OPTIONS', pp, TOKEN_A)
    if a or st != 404:
        cnt += 1
        print('OPTIONS %-80s %s allow=%s' % (pp, st, a or '-'))
print('non-404/with-allow count:', cnt)
print('done')
