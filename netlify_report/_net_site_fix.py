# -*- coding: utf-8 -*-
"""检查 SITE_A custom_domain 状态并恢复为 null"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()
H = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
     'Accept': 'application/json', 'Authorization': 'Bearer ' + TOKEN_A,
     'Content-Type': 'application/json'}

def req(method, path, body=None, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=H)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

st, b = req('GET', '/api/v1/sites/' + SITE_A)
j = json.loads(b)
print('GET custom_domain =', repr(j.get('custom_domain')))
print('GET domains =', j.get('domains'))
print('GET ssl =', str(j.get('ssl'))[:100])
print('state =', j.get('state'))

if j.get('custom_domain') not in (None, '', 'None'):
    st, b = req('PATCH', '/api/v1/sites/' + SITE_A, {'custom_domain': None})
    print('PATCH custom_domain=null ->', st, b[:150])
    st, b = req('GET', '/api/v1/sites/' + SITE_A)
    j2 = json.loads(b)
    print('after null: custom_domain =', repr(j2.get('custom_domain')))
else:
    print('custom_domain already clean')
