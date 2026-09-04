# -*- coding: utf-8 -*-
"""Netlify:zip 方式部署"""
import http.client, ssl, gzip, brotli, sys, json, io, zipfile, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=60)
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

# 1. 构建 zip
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('index.html', '<html><body>SEC TEST <img src="/.netlify/images?url=https://example.com/x.png"></body></html>')
    z.writestr('test.txt', 'hello netlify test')
    z.writestr('_headers', '/secret.json\n  X-Test: 1\n')
    z.writestr('_redirects', '/old /new 301\n')
    z.writestr('secret.json', '{"secret":"local-test"}')
zip_bytes = buf.getvalue()
print('zip size:', len(zip_bytes))

# 2. 创建 deploy(zip 原始 body)
s, raw = api('/api/v1/sites/%s/deploys' % SITE_ID, method='POST',
             raw_body=zip_bytes, ctype='application/zip')
print('create deploy:', s, raw[:200].decode('utf-8', 'ignore'))
d = json.loads(raw)
deploy_id = d.get('id')
print('deploy_id:', deploy_id, 'state:', d.get('state'))

# 3. 发布
s, raw = api('/api/v1/deploys/%s' % deploy_id, method='POST', body={})
print('publish:', s, raw[:200].decode('utf-8', 'ignore'))
if s == 200:
    print('published state:', json.loads(raw).get('state'))
    print('url:', json.loads(raw).get('ssl_url'))
