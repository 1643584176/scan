# -*- coding: utf-8 -*-
"""Netlify:函数上传完整状态链 new->uploaded->publish + 探测"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()
DID = '6a97b9f4c3a18ded7e5216fa'

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

# 1. 先看 deploy 状态
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
d = json.loads(raw)
print('state now:', d.get('state'), '| required_functions:', d.get('required_functions'))
print('  summary:', json.dumps({k: d.get(k) for k in ['state', 'name', 'commit_ref']}))

# 2. PUT 一个 index.html 文件
s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT',
             raw_body=b'<html>probe</html>', ctype='text/html')
print('put file:', s, raw[:80].decode('utf-8', 'ignore'))

# 3. 看状态
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
d = json.loads(raw)
print('state after file:', d.get('state'))

# 4. 传函数
FN_CODE = open(r'D:\scan\netlify_report\_fn_probe.js', encoding='utf-8').read() if False else None
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', 'exports.handler = async () => { return { statusCode: 200, body: "ok" }; };')
zb = buf.getvalue()
s, raw = api('/api/v1/deploys/%s/functions/probe1' % DID, method='PUT', raw_body=zb,
             ctype='application/zip', qs='?runtime=js&size=%d' % len(zb))
print('upload fn:', s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' '))

# 5. 状态 + 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID))
d = json.loads(raw)
print('state after fn:', d.get('state'), '| functions:', d.get('functions'))
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
d = json.loads(raw) if s == 200 else {}
print('publish:', s, 'final state:', d.get('state'), 'functions:', json.dumps(d.get('functions'))[:200])
