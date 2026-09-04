# -*- coding: utf-8 -*-
"""Netlify:创建测试站点,获得 siteId"""
import http.client, ssl, gzip, brotli, json, sys, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

ctx = ssl.create_default_context()

def api(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
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

name = 'sec-test-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
print('site name:', name)
s, raw = api('/api/v1/sites', method='POST', body={'name': name})
print('POST /api/v1/sites:', s)
print(' ', raw[:400].decode('utf-8', 'ignore').replace('\n', ' '))
if s in (200, 201):
    d = json.loads(raw)
    print('SITE_ID:', d.get('id'))
    print('SITE_URL:', d.get('url'))
    print('SITE_SSL:', d.get('ssl_url'))
    open(r'D:\scan\netlify_report\_js\net_site.json', 'w', encoding='utf-8').write(raw.decode('utf-8', 'ignore'))
else:
    # 试试 account slug 路径
    s2, raw2 = api('/api/v1/1643584176/sites', method='POST', body={'name': name})
    print('POST /{slug}/sites:', s2)
    print(' ', raw2[:400].decode('utf-8', 'ignore').replace('\n', ' '))
