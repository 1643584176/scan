# -*- coding: utf-8 -*-
"""拿 A/B 账号列表(teamId),然后 identeer/fetch-site-config/agent-file-delete 交叉探测"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def api(token):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token}
    conn.request('GET', '/api/v1/accounts', headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


def fn(path, cookie=True):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:600].decode('utf-8', 'ignore')
    conn.close()
    return st, out


st, out = api(TOKEN_A)
print('A accounts [%d] %s' % (st, out[:400]))
st, out = api(TOKEN_B)
print('B accounts [%d] %s' % (st, out[:400]))
