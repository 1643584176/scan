# -*- coding: utf-8 -*-
"""Netlify:zip 创建(带函数目录)后第一请求即 PUT functions bundle,快速重试窗口"""
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

# 1. zip 创建(index.html + 函数源码,制造稍慢的处理)
site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', '<html><body>fn11</body></html>')
    z.writestr('netlify/functions/probe2/index.js', probe2_src)
    z.writestr('robots.txt', 'User-agent: *\nDisallow: /')
site_zip = site_buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
d = json.loads(raw)
DID = d.get('id')
print('create:', s, 'DID:', DID, 'state:', d.get('state'))

# 2. 函数 bundle zip
zbuf = io.BytesIO()
with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', probe2_src)
    z.writestr('package.json', json.dumps({'name': 'probe2', 'version': '1.0.0', 'main': 'index.js'}))
fzip = zbuf.getvalue()

# 3. 立即重试 PUT(0ms 开始,共 20 次)
ok = False
for i in range(20):
    s2, raw2 = api('/api/v1/deploys/%s/functions/probe2' % DID, method='PUT', raw_body=fzip,
                   ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
    msg = raw2[:160].decode('utf-8', 'ignore').replace('\n', ' ')
    print('PUT try %d: %d %s' % (i, s2, msg))
    if s2 == 200:
        ok = True
        break
    time.sleep(0.5)

if ok:
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
    dd = json.loads(raw) if s == 200 else {}
    print('publish:', s, dd.get('state'))
    time.sleep(3)
    try:
        conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=60)
        conn.request('GET', '/.netlify/functions/probe2')
        r = conn.getresponse()
        b = r.read()
        print('invoke:', r.status, 'len', len(b))
        print(b[:1500].decode('utf-8', 'ignore'))
        conn.close()
    except Exception as e:
        print('invoke err:', str(e)[:150])
else:
    print('ALL PUT FAILED; state dump:')
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
    print(raw[:300].decode('utf-8', 'ignore'))
