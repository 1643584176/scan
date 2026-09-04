# -*- coding: utf-8 -*-
"""Netlify:deploy state 转换测试"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
DEPLOY_ID = '6a97a3394abd4187ed7cadfa'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
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

# PUT 更新 deploy:尝试 state 字段
for body in [{'state': 'uploading'}, {'draft': True}, {'draft': False, 'state': 'uploading'}]:
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_ID, DEPLOY_ID), method='PUT', body=body)
    print('PUT deploy %s: %d %s' % (body, s, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')))
    if s == 200:
        print('  new state:', json.loads(raw).get('state'))
        # 试上传
        s2, raw2 = api('/api/v1/deploys/%s/files/index.html?size=30' % DEPLOY_ID,
                       method='PUT', raw_body=b'<html><body>SEC TEST</body></html>', ctype='application/octet-stream')
        print('  upload: %d %s' % (s2, raw2[:100].decode('utf-8', 'ignore')))
        if s2 == 200:
            break
