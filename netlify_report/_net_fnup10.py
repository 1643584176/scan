# -*- coding: utf-8 -*-
"""Netlify:PUT files 方式推进状态机 new->uploading->uploaded,窗口内 PUT 函数 bundle"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs=''):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
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

probe2_src = open(r'D:\scan\netlify_report\_fn_probe2.js', encoding='utf-8').read()

# 1. JSON 创建 deploy
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body={'title': 'fn-files'})
d = json.loads(raw)
DID = d.get('id')
print('create:', s, 'DID:', DID, 'state:', d.get('state'))

# 2. PUT index.html 文件
html = b'<html><body>fn files</body></html>'
s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html,
             ctype='application/octet-stream', qs='?size=%d' % len(html))
print('put index.html:', s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' '))

# 3. 轮询状态 + uploaded 窗口 PUT 函数
zbuf = io.BytesIO()
with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', probe2_src)
fzip = zbuf.getvalue()

last = None
for i in range(60):
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
    dd = json.loads(raw)
    st = dd.get('state')
    if st != last:
        print('t+%.1fs state=%s files=%s' % (i * 0.3, st, json.dumps(dd.get('files'))[:150]))
        last = st
    if st in ('uploaded', 'uploading', 'ready'):
        s2, raw2 = api('/api/v1/deploys/%s/functions/probe2' % DID, method='PUT', raw_body=fzip,
                       ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        print('  PUT fn @%s: %d %s' % (st, s2, raw2[:150].decode('utf-8', 'ignore').replace('\n', ' ')))
        if s2 == 200:
            print('PUT OK!')
            break
    time.sleep(0.3)
