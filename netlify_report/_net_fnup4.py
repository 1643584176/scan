# -*- coding: utf-8 -*-
"""Netlify:向 uploaded deploy 上传函数 + 发布 + 调用"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()
DID = '6a97ba24c3a18decdb521709'

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', host='api.netlify.com'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=60)
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

# 1. 探测函数 zip
FN = 'exports.handler = async () => ({ statusCode: 200, body: "probe-ok" });'
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', FN)
zb = buf.getvalue()

s, raw = api('/api/v1/deploys/%s/functions/probe1' % DID, method='PUT', raw_body=zb,
             ctype='application/zip', qs='?runtime=js&size=%d' % len(zb))
print('upload fn zip:', s, raw[:200].decode('utf-8', 'ignore').replace('\n', ' '))

# 2. 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
d = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', d.get('state'), 'functions:', json.dumps(d.get('functions'))[:300])

# 3. 调用(站点域)
try:
    conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=30)
    conn.request('GET', '/.netlify/functions/probe1')
    r = conn.getresponse()
    b = r.read()
    print('invoke fn:', r.status, b[:200].decode('utf-8', 'ignore'))
    conn.close()
except Exception as e:
    print('invoke err:', str(e)[:100])
