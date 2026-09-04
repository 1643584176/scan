# -*- coding: utf-8 -*-
"""Netlify:probe2 部署实验 - zip 含函数源码目录(.netlify/functions),轮询状态抢 uploaded 窗口 PUT 函数"""
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

FN_CODE = open(r'D:\scan\netlify_report\_fn_probe2.js', encoding='utf-8').read()

def state_of(did):
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, did))
    if s != 200:
        return None, raw[:100]
    d = json.loads(raw)
    return d.get('state'), d.get('functions')

# 1. zip 创建 deploy:index.html + netlify/functions/probe2/index.js(源码,无点前缀)
site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', '<html><body>fn probe2</body></html>')
    z.writestr('netlify/functions/probe2/index.js', FN_CODE)
site_zip = site_buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
d = json.loads(raw)
DID = d.get('id')
print('create deploy:', s, 'id:', DID, 'state:', d.get('state'))
print('required_functions:', d.get('required_functions'))

# 2. 函数 bundle zip(含 package.json? zip-it-and-ship-it 格式:index.js 顶层)
zbuf = io.BytesIO()
with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', FN_CODE)
    z.writestr('package.json', json.dumps({'name': 'probe2', 'version': '1.0.0', 'main': 'index.js'}))
fzip = zbuf.getvalue()
print('fn zip size:', len(fzip))

# 3. 并发:轮询状态 + 尝试 PUT 函数(抢窗口)
last_state = None
for i in range(60):
    st_now, funcs = state_of(DID)
    if st_now != last_state:
        print('t+%.1fs state=%s functions=%s' % (i * 0.2, st_now, json.dumps(funcs)[:200]))
        last_state = st_now
    if st_now in ('uploaded', 'uploading'):
        s, raw = api('/api/v1/deploys/%s/functions/probe2' % DID, method='PUT', raw_body=fzip,
                     ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        print('PUT fn at t+%.1fs: %d %s' % (i * 0.2, s, raw[:200].decode('utf-8', 'ignore').replace('\n', ' ')))
        if s == 200:
            break
    time.sleep(0.2)

# 4. 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'), 'functions:', json.dumps(dd.get('functions'))[:400])

# 5. 调用
time.sleep(2)
try:
    conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=90)
    conn.request('GET', '/.netlify/functions/probe2')
    r = conn.getresponse()
    b = r.read()
    print('invoke status:', r.status, 'len:', len(b))
    print(b[:3000].decode('utf-8', 'ignore'))
    conn.close()
except Exception as e:
    print('invoke err:', str(e)[:200])
