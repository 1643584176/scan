# -*- coding: utf-8 -*-
"""收集: 1) 泄露 site_id 可读性  2) A 站 NXDOMAIN 域绑定后的证书状态机"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A, COOKIE_A

ctx = ssl.create_default_context()
LEAK_SITE = 'a0adc15c-3f90-49a8-acb4-3ec6d1e19e3c'

def req(host, path, token=None, cookie=None, timeout=20):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    if cookie: h['Cookie'] = cookie
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

print('== 1. 泄露的 site_id 可读性 ==')
for lbl, host, path, tok, ck in [
    ('A token GET /api/v1/sites/leak',     'api.netlify.com', '/api/v1/sites/' + LEAK_SITE, TOKEN_A, None),
    ('A cookie GET /api/v1/sites/leak',    'api.netlify.com', '/api/v1/sites/' + LEAK_SITE, None, COOKIE_A),
    ('anon   GET /api/v1/sites/leak',      'api.netlify.com', '/api/v1/sites/' + LEAK_SITE, None, None),
    ('A token GET /api/v1/sites/leak/domain', 'api.netlify.com', '/api/v1/sites/' + LEAK_SITE + '/domain', TOKEN_A, None),
]:
    st, b = req(host, path, tok, ck)
    print('%-40s %s | %s' % (lbl, st, b[:200]))

print()
print('== 2. A 站 NXDOMAIN 域状态机(绑定后 ~15min) ==')
st, b = req('api.netlify.com', '/api/v1/sites/' + SITE_A, TOKEN_A)
try:
    j = json.loads(b)
    for k in ['custom_domain', 'domains', 'state', 'ssl', 'ssl_plan', 'ssl_url', 'url']:
        if k in j:
            print('%-14s = %s' % (k, str(j[k])[:200]))
except Exception:
    print('parse fail', b[:300])

print()
print('== 3. 探测 example.com 占主站点的域名(站点列表里找) ==')
st, b = req('api.netlify.com', '/api/v1/sites/' + SITE_A + '/domains', TOKEN_A)
print('my domains:', st, b[:200])
