# -*- coding: utf-8 -*-
"""Netlify:用 zip-it-and-ship-it 标准产物(zip 顶层含 {name}.js 引导)重新部署 probe1/probe2"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
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

zips = {}
for name in ('probe1', 'probe2'):
    with open(r'D:\scan\netlify_report\_zisi\out2\%s.zip' % name, 'rb') as f:
        zips[name] = f.read()
    print(name, 'zip bytes:', len(zips[name]))

html = b'<html><body>zisi-fmt</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
functions = {name: hashlib.sha256(z).hexdigest() for name, z in zips.items()}

# 1. 创建 deploy(files + functions 预算)
body = {'title': 'fn-zisi', 'files': files, 'functions': functions}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body=body)
d = json.loads(raw)
DID = d.get('id')
print('create:', s, 'DID:', DID, 'state:', d.get('state'), '| required_functions:', json.dumps(d.get('required_functions'))[:200])

# 2. 上传 index.html
s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html,
             ctype='application/octet-stream', qs='?size=%d' % len(html))
print('put file:', s, raw[:100].decode('utf-8', 'ignore').replace('\n', ' '))

# 3. PUT 函数 bundle(轮询直到 200 或终态)
done = {}
for name, fzip in zips.items():
    for i in range(30):
        s2, raw2 = api('/api/v1/deploys/%s/functions/%s' % (DID, name), method='PUT', raw_body=fzip,
                       ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        if s2 == 200:
            print('PUT fn %s OK: %s' % (name, raw2[:200].decode('utf-8', 'ignore').replace('\n', ' ')))
            done[name] = True
            break
        print('  PUT %s try%d: %d %s' % (name, i, s2, raw2[:150].decode('utf-8', 'ignore').replace('\n', ' ')))
        time.sleep(0.5)

# 4. 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
dd = json.loads(raw)
print('state before publish:', dd.get('state'))
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'), '| url:', dd.get('deploy_ssl_url', '')[:60])
if dd.get('available_functions'):
    print('available_functions:', json.dumps(dd['available_functions'])[:400])

# 5. 调用验证
time.sleep(5)
for name in done:
    try:
        conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=60)
        conn.request('GET', '/.netlify/functions/%s' % name)
        r = conn.getresponse()
        b = r.read()
        print('invoke', name, ':', r.status, 'len', len(b))
        if r.status == 200:
            print(b[:4500].decode('utf-8', 'ignore'))
        conn.close()
    except Exception as e:
        print('invoke', name, 'err:', str(e)[:150])
