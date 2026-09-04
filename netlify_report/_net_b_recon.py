# -*- coding: utf-8 -*-
"""Netlify:账号 B 侦察 - sites 列表 / 配额状态"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()

def api(host, path, token, method='GET', body=None, raw_body=None, ctype='application/json', qs='', timeout=25):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
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
s, raw = api('api.netlify.com', '/api/v1/user', TOKEN_B)
print('user:', s, raw[:200].decode('utf-8', 'replace'))
# 2. accounts
s, raw = api('api.netlify.com', '/api/v1/accounts', TOKEN_B)
print('accounts:', s, raw[:400].decode('utf-8', 'replace'))
# 3. sites
s, raw = api('api.netlify.com', '/api/v1/sites?per_page=20', TOKEN_B)
print('sites:', s, raw[:600].decode('utf-8', 'replace'))
