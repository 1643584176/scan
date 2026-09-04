# -*- coding: utf-8 -*-
"""Netlify:probe2 部署 - zip 创建后立刻轮询 PUT 函数(抢 uploaded 窗口)"""
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

# 1. zip 创建 deploy(index.html 占位)
site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', '<html><body>fn probe2</body></html>')
site_zip = site_buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
d = json.loads(raw)
DID = d.get('id')
print('create deploy:', s, 'id:', DID, 'state:', d.get('state'))

# 2. 轮询 PUT 函数(uploaded 窗口)
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', FN_CODE)
zb = buf.getvalue()
print('fn zip size:', len(zb))

ok = False
for i in range(30):
    s, raw = api('/api/v1/deploys/%s/functions/probe2' % DID, method='PUT', raw_body=zb,
                 ctype='application/zip', qs='?runtime=js&size=%d' % len(zb))
    if s == 200:
        print('upload fn OK at try', i, '->', raw[:200].decode('utf-8', 'ignore').replace('\n', ' '))
        ok = True
        break
    if i % 5 == 0:
        print('try', i, ':', s, raw[:100].decode('utf-8', 'ignore').replace('\n', ' '))
    time.sleep(0.3)
if not ok:
    print('FAILED upload fn; dump deploy state:')
    s2, raw2 = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
    print(' ', s2, raw2[:400].decode('utf-8', 'ignore'))
    sys.exit(1)

# 3. 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'), 'functions:', json.dumps(dd.get('functions'))[:400])

# 4. 调用
time.sleep(2)
try:
    conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=90)
    conn.request('GET', '/.netlify/functions/probe2')
    r = conn.getresponse()
    b = r.read()
    print('invoke status:', r.status, 'len:', len(b))
    try:
        dd2 = json.loads(b)
        print(json.dumps(dd2, indent=1, ensure_ascii=False)[:8000])
    except Exception:
        print(b[:3000].decode('utf-8', 'ignore'))
    conn.close()
except Exception as e:
    print('invoke err:', str(e)[:200])
