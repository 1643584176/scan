# -*- coding: utf-8 -*-
"""查看 A team member 完整对象 + account 信息(plan/roles)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

def req(method, path, token=TOKEN_A, timeout=25):
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
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

st, b = req('GET', '/api/v1/1643584176/members')
print('members full:')
print(json.dumps(json.loads(b), indent=1)[:2500])
print()
st, b = req('GET', '/api/v1/accounts')
print('accounts:', b[:1500])
print()
st, b = req('GET', '/api/v1/1643584176')
print('/{slug}:', b[:1500])
