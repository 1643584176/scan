# -*- coding: utf-8 -*-
"""Netlify:验证 zip 含 netlify/functions 后 deploy 是否保持 uploaded;保持则 PUT bundle"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io, time
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

site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w') as z:
    z.writestr('index.html', '<html><body>fn probe2</body></html>')
    z.writestr('netlify/functions/probe2/index.js', probe2_src)
site_zip = site_buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
d = json.loads(raw)
DID = d.get('id')
print('create deploy:', s, 'id:', DID, 'state:', d.get('state'))

# 轮询 30s 观察状态(不 publish)
for i in range(30):
    time.sleep(1)
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
    d = json.loads(raw)
    st = d.get('state')
    print('t+%ds state=%s' % (i + 1, st))
    if st != 'uploaded':
        break
    # 在 uploaded 时尝试 PUT 函数
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('index.js', probe2_src)
    fzip = zbuf.getvalue()
    s2, raw2 = api('/api/v1/deploys/%s/functions/probe2' % DID, method='PUT', raw_body=fzip,
                   ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
    print('   PUT fn: %d %s' % (s2, raw2[:150].decode('utf-8', 'ignore').replace('\n', ' ')))
    if s2 == 200:
        print('PUT OK!')
        break
