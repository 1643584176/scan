# -*- coding: utf-8 -*-
"""Netlify:恢复 probe1 + 部署 probe2 - zip 内 netlify/functions/*/index.js 源码方式(复刻 fnup3 成功案例,ZIP_STORED)"""
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

probe1_src = open(r'D:\scan\netlify_report\fn_functions\probe1\index.js', encoding='utf-8').read()
probe2_src = open(r'D:\scan\netlify_report\_fn_probe2.js', encoding='utf-8').read()

# zip 创建 deploy(ZIP_STORED,复刻 fnup3)
site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w') as z:  # ZIP_STORED 默认
    z.writestr('index.html', '<html><body>fn probe</body></html>')
    z.writestr('netlify/functions/probe1/index.js', probe1_src)
    z.writestr('netlify/functions/probe2/index.js', probe2_src)
site_zip = site_buf.getvalue()
print('zip size:', len(site_zip))
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
print('create deploy:', s, raw[:300].decode('utf-8', 'ignore').replace('\n', ' '))
d = json.loads(raw)
DID = d.get('id')
print('deploy id:', DID, 'state:', d.get('state'))
print('required_functions:', d.get('required_functions'))

# 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'))

# 等待构建+轮询调用
for name in ['probe1', 'probe2']:
    for i in range(30):
        time.sleep(2)
        try:
            conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=30)
            conn.request('GET', '/.netlify/functions/%s' % name)
            r = conn.getresponse()
            b = r.read()
            conn.close()
            if r.status == 200:
                print(name, '=> 200 len', len(b))
                break
            print(name, 'try', i, '=>', r.status)
        except Exception as e:
            print(name, 'try', i, 'err', str(e)[:80])
open(r'D:\scan\netlify_report\_js\net_fn_deploy3.json', 'w').write(json.dumps({'deploy_id': DID}))
