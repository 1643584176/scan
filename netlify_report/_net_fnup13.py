# -*- coding: utf-8 -*-
"""Netlify:CLI 式部署 - files 预算创建(uploading)后 PUT files + PUT functions bundle + 发布"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs=''):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
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

def mk_zip(src):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('index.js', src)
    return buf.getvalue()

# 1. files 预算创建
html = b'<html><body>cli-like</body></html>'
body = {'title': 'fn-recover2', 'files': {'/index.html': hashlib.sha1(html).hexdigest()}}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body=body)
d = json.loads(raw)
DID = d.get('id')
print('create:', s, 'DID:', DID, 'state:', d.get('state'))

# 2. 上传 index.html
s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html,
             ctype='application/octet-stream', qs='?size=%d' % len(html))
print('put file:', s, raw[:120].decode('utf-8', 'ignore').replace('\n', ' '))

# 3. PUT 函数 bundle(轮询重试,直到成功或状态终态)
done = {}
for name, src in [('probe1', probe1_src), ('probe2', probe2_src)]:
    fzip = mk_zip(src)
    for i in range(20):
        s2, raw2 = api('/api/v1/deploys/%s/functions/%s' % (DID, name), method='PUT', raw_body=fzip,
                       ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        if s2 == 200:
            print('PUT fn %s OK: %s' % (name, raw2[:200].decode('utf-8', 'ignore').replace('\n', ' ')))
            done[name] = True
            break
        print('  PUT %s try%d: %d %s' % (name, i, s2, raw2[:130].decode('utf-8', 'ignore').replace('\n', ' ')))
        time.sleep(0.4)

# 4. 检查状态 + 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
dd = json.loads(raw)
print('state before publish:', dd.get('state'), '| available_functions:', json.dumps(dd.get('available_functions'))[:300])
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'))

# 5. 调用
time.sleep(4)
for name in done:
    try:
        conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=60)
        conn.request('GET', '/.netlify/functions/%s' % name)
        r = conn.getresponse()
        b = r.read()
        print('invoke', name, ':', r.status, 'len', len(b))
        if name == 'probe2' and r.status == 200:
            print(b[:4000].decode('utf-8', 'ignore'))
        conn.close()
    except Exception as e:
        print('invoke', name, 'err:', str(e)[:120])
