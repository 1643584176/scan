# -*- coding: utf-8 -*-
"""完整 dump SITE_A 站点 JSON + sites 列表 JSON, 找未文档化字段"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

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

st, b = req('GET', '/api/v1/sites/%s' % SITE_A)
d = json.loads(b)
print('== SITE_A 顶层字段 ==')
for k, v in d.items():
    vs = json.dumps(v)[:150] if not isinstance(v, str) else v[:150]
    print('%-34s %s' % (k, vs))

print()
print('== 嵌套对象 keys ==')
for k, v in d.items():
    if isinstance(v, dict):
        print('%s -> %s' % (k, list(v.keys())))
    elif isinstance(v, list) and v and isinstance(v[0], dict):
        print('%s[0] -> %s' % (k, list(v[0].keys())))
print('done')
