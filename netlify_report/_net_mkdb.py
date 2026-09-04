# -*- coding: utf-8 -*-
"""Netlify:为测试站点创建数据库"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
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

# 1. 查看当前数据库状态
s, raw = api('/api/v1/sites/%s/database' % SITE_ID)
print('GET database:', s, raw[:200].decode('utf-8', 'ignore'))

# 2. 创建数据库(默认 postgres)
s, raw = api('/api/v1/sites/%s/database' % SITE_ID, method='POST', body={})
print('POST database:', s, raw[:300].decode('utf-8', 'ignore'))

# 3. 查看
s, raw = api('/api/v1/sites/%s/database' % SITE_ID)
print('GET database again:', s, raw[:300].decode('utf-8', 'ignore'))
