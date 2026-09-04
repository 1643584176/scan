# -*- coding: utf-8 -*-
"""查当前 jwks provider 列表 + auth 配置"""
import json, http.client, ssl, sys

sys.path.insert(0, '.')
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open('_apikey.json', encoding='utf-8'))['key']

def req(method, path, body=None, tmo=20):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

st, raw = req('GET', '/projects/%s/jwks' % P)
print('GET jwks:', st)
print(raw.decode(errors='replace')[:2000], flush=True)

# 分支级 auth 配置
B = 'br-wandering-field-w2ob6mpn'
st, raw = req('GET', '/projects/%s/branches/%s/auth' % (P, B))
print('\nGET branch auth:', st)
print(raw.decode(errors='replace')[:1000], flush=True)
