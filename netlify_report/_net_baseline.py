# -*- coding: utf-8 -*-
"""Netlify:账号基线(user/accounts/members/sites)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, extra=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER}
    if extra:
        h.update(extra)
    conn.request(method, path, body=body, headers=h)
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

# 1. user
s, raw = api('/api/v1/user')
print('user:', s)
u = json.loads(raw) if s == 200 else {}
for k in ['id', 'email', 'full_name', 'uid', 'affiliate_id', 'created_at']:
    if k in u:
        print('  %s: %s' % (k, u[k]))
open(r'D:\scan\netlify_report\_js\net_user.json', 'w', encoding='utf-8').write(raw.decode('utf-8', 'ignore'))
print()

# 2. accounts
s, raw = api('/api/v1/accounts')
print('accounts:', s)
if s == 200:
    accs = json.loads(raw)
    for a in accs:
        print('  id=%s slug=%s name=%s type=%s roles=%s' % (
            a.get('id'), a.get('slug'), a.get('name'), a.get('type'),
            ','.join(a.get('roles_allowed') or [])))
        # 保存 account id
        globals()['ACC_ID'] = a.get('id')
print()

# 3. members
s, raw = api('/api/v1/1643584176/members')
print('members (slug=1643584176):', s)
if s == 200:
    for m in (json.loads(raw) or [])[:5]:
        print('  id=%s email=%s role=%s' % (m.get('id'), m.get('email'), m.get('role')))
print()

# 4. sites
s, raw = api('/api/v1/sites?per_page=10')
print('sites:', s)
if s == 200:
    sites = json.loads(raw)
    print('  count:', len(sites))
    for st_ in sites:
        print('  id=%s name=%s url=%s' % (st_.get('id'), st_.get('name'), st_.get('url')))
else:
    print('  ', raw[:150].decode('utf-8', 'ignore'))
