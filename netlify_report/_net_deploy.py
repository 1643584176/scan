# -*- coding: utf-8 -*-
"""Netlify:上传部署(含 HTML + edge function),激活站点域平台路径"""
import http.client, ssl, gzip, brotli, sys, json, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER, 'Content-Type': ctype}
    payload = body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
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

# 1. 创建 deploy(获取 upload_url + required files)
s, raw = api('/api/v1/sites/%s/deploys' % SITE_ID, method='POST', body={'title': 'sec test'})
print('create deploy:', s, raw[:200].decode('utf-8', 'ignore'))
d = json.loads(raw)
deploy_id = d.get('id')
upload_url = d.get('ssl_url') or d.get('deploy_ssl_url')
print('deploy_id:', deploy_id)

# 2. 上传文件
files = {
    'index.html': b'<html><body>SEC TEST <img src="/.netlify/images?url=https://example.com/x.png"></body></html>',
    'test.txt': b'hello netlify test',
    'secret.json': b'{"secret":"local-test"}',
}
for fname, content in files.items():
    h = hashlib.sha1(content).hexdigest()
    s, raw = api('/api/v1/deploys/%s/files/%s' % (deploy_id, fname), method='PUT', raw_body=content, ctype='application/octet-stream')
    print('upload %s: %d %s' % (fname, s, raw[:80].decode('utf-8', 'ignore')))

# 3. 触发发布
s, raw = api('/api/v1/deploys/%s' % deploy_id, method='POST', body={})
print('publish:', s, raw[:150].decode('utf-8', 'ignore'))
