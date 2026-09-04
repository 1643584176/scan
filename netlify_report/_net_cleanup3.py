# -*- coding: utf-8 -*-
"""删 dns zone 残留 + 尝试推进 draft deploy 状态以便删除"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
DRAFTS = ['6a97f0a3d140c41a6e99d484', '6a97ee98dbddc51205172efc',
          '6a97ee7704f63e090a31fa90', '6a97ee5078dff32c88aa39aa']

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

print('== 1. 删 dns zone 残留 ==')
st, b = req('DELETE', '/api/v1/dns_zones/6a97ecc68ea37900af43734c')
print('DELETE zone:', st, b[:100])
st, b = req('GET', '/api/v1/dns_zones')
print('GET zones:', st, b[:100])

print()
print('== 2. draft 状态推进(PUT /sites/{id}/deploys/{did})==')
for did in DRAFTS[:1]:
    for body in [{'state': 'uploading'}, {'state': 'ready'}, {'draft': False}]:
        st, b = req('PUT', '/api/v1/sites/%s/deploys/%s' % (SITE_A, did), body)
        print('PUT %s %s -> %s | %s' % (did[:8], body, st, b[:150].replace('\n', ' ')))
    # 推进后删除尝试
    st, b = req('DELETE', '/api/v1/sites/%s/deploys/%s' % (SITE_A, did))
    print('DELETE after try:', st, b[:150])
print('done')
