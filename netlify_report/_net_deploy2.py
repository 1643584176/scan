# -*- coding: utf-8 -*-
"""Netlify:部署重试(带 body + size)"""
import http.client, ssl, gzip, brotli, sys, json, hashlib, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
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

# 1. 创建 deploy 带 body
s, raw = api('/api/v1/sites/%s/deploys' % SITE_ID, method='POST', body={})
print('create deploy:', s, raw[:250].decode('utf-8', 'ignore'))
d = json.loads(raw)
deploy_id = d.get('id')
print('deploy_id:', deploy_id, 'state:', d.get('state'))

# 2. 上传文件(带 size)
files = {
    'index.html': b'<html><body>SEC TEST</body></html>',
    'test.txt': b'hello netlify test',
}
for fname, content in files.items():
    s, raw = api('/api/v1/deploys/%s/files/%s?size=%d' % (deploy_id, fname, len(content)),
                 method='PUT', raw_body=content, ctype='application/octet-stream')
    print('upload %s: %d %s' % (fname, s, raw[:100].decode('utf-8', 'ignore')))

# 3. 查看状态
s, raw = api('/api/v1/deploys/%s' % deploy_id)
print('deploy state:', s, json.loads(raw).get('state') if s == 200 else raw[:100])

# 4. 发布
s, raw = api('/api/v1/deploys/%s' % deploy_id, method='POST', body={})
print('publish:', s, raw[:150].decode('utf-8', 'ignore'))
