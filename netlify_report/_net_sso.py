# -*- coding: utf-8 -*-
"""Netlify:关闭站点 SSO 保护"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER, 'Content-Type': 'application/json'}
    payload = json.dumps(body).encode() if body is not None else None
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

s, raw = api('/api/v1/sites/%s' % SITE_ID, method='PUT', body={
    'sso_login': False,
    'sso_login_context': 'off',
    'account_sso_login': False,
})
print('PUT site:', s, raw[:250].decode('utf-8', 'ignore'))
d = json.loads(raw) if s == 200 else {}
print('sso_login:', d.get('sso_login'), 'sso_login_context:', d.get('sso_login_context'))
