# -*- coding: utf-8 -*-
"""Netlify:完整 dump site/user/account 响应,找内部字段"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def api(path, method='GET'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER}
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# site 完整 JSON
s, raw = api('/api/v1/sites/%s' % SITE_ID)
d = json.loads(raw)
print('=== site keys ===')
print(sorted(d.keys()))
# 敏感/内部字段
for k in sorted(d.keys()):
    v = d[k]
    if isinstance(v, str) and ('http' in v.lower() or 'token' in k.lower() or 'key' in k.lower() or 'secret' in k.lower()):
        print('  %s: %s' % (k, str(v)[:120]))
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            if isinstance(v2, str) and ('token' in k2.lower() or 'key' in k2.lower() or 'secret' in k2.lower()):
                print('  %s.%s: %s' % (k, k2, str(v2)[:120]))
open(r'D:\scan\netlify_report\_js\net_site_full.json', 'w', encoding='utf-8').write(json.dumps(d, indent=1))

# user 完整 JSON
s, raw = api('/api/v1/user')
u = json.loads(raw)
print()
print('=== user keys ===')
print(sorted(u.keys()))
open(r'D:\scan\netlify_report\_js\net_user_full.json', 'w', encoding='utf-8').write(json.dumps(u, indent=1))

# account 完整 JSON
s, raw = api('/api/v1/accounts/1643584176')
a = json.loads(raw)
print()
print('=== account keys ===')
print(sorted(a.keys()))
open(r'D:\scan\netlify_report\_js\net_account_full.json', 'w', encoding='utf-8').write(json.dumps(a, indent=1))
