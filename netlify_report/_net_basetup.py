# -*- coding: utf-8 -*-
"""Netlify:账号 B 基线 + 建站 + 建库(越权对测准备)"""
import http.client, ssl, gzip, brotli, sys, json, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', token=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + (token or TOKEN_B), 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
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
    return st, raw

# 1. user
s, raw = api('/api/v1/user')
print('user:', s)
u = json.loads(raw) if s == 200 else {}
for k in ['id', 'email', 'full_name']:
    if k in u:
        print('  %s: %s' % (k, u[k]))

# 2. accounts
s, raw = api('/api/v1/accounts')
print('accounts:', s)
accs = json.loads(raw) if s == 200 else []
for a in accs:
    print('  id=%s slug=%s name=%s type=%s roles=%s' % (
        a.get('id'), a.get('slug'), a.get('name'), a.get('type'), a.get('roles_allowed')))
    ACC_B_ID = a.get('id')

# 3. 建站
name = 'sec-b-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
s, raw = api('/api/v1/sites', method='POST', body={'name': name})
print('create site B:', s)
d = json.loads(raw) if s in (200, 201) else {}
SITE_B = d.get('id')
print('  SITE_B:', SITE_B, 'url:', d.get('ssl_url'))
if d.get('sso_login'):
    # 关 SSO
    s2, raw2 = api('/api/v1/sites/%s' % SITE_B, method='PUT',
                   body={'sso_login': False, 'sso_login_context': 'all'})
    print('  sso off:', s2)

# 4. 建库
if SITE_B:
    s, raw = api('/api/v1/sites/%s/database' % SITE_B, method='POST', body={})
    print('create database B:', s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' '))
    open(r'D:\scan\netlify_report\_js\net_site_b.json', 'w', encoding='utf-8').write(
        json.dumps({'site_id': SITE_B, 'account_id': ACC_B_ID, 'name': name}, indent=1))
    print('saved site B info')
