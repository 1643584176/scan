# -*- coding: utf-8 -*-
"""Netlify:账号 B 部署 probe-log 单函数(新 deploy)"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_B, 'Content-Type': ctype}
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

name = 'probe-log'
with open(r'D:\scan\netlify_report\_zisi\out3\%s.zip' % name, 'rb') as f:
    fzip = f.read()
print('zip bytes:', len(fzip), flush=True)

html = b'<html><body>siteB</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
functions = {name: hashlib.sha256(fzip).hexdigest()}

body = {'title': 'fn-plog', 'files': files, 'functions': functions}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_B, method='POST', body=body)
print('create:', s, raw[:300].decode('utf-8', 'replace'), flush=True)
if s != 200:
    sys.exit(1)
d = json.loads(raw)
DID = d.get('id')
print('DID:', DID, 'state:', d.get('state'), flush=True)

s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html,
             ctype='application/octet-stream', qs='?size=%d' % len(html))
print('put file:', s, flush=True)

for i in range(10):
    s2, raw2 = api('/api/v1/deploys/%s/functions/%s' % (DID, name), method='PUT', raw_body=fzip,
                   ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
    if s2 == 200:
        print('PUT fn OK', flush=True)
        break
    print('PUT try%d: %d %s' % (i, s2, raw2[:150].decode('utf-8', 'ignore').replace('\n', ' ')), flush=True)
    time.sleep(0.5)

s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_B, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'), flush=True)
if dd.get('available_functions'):
    print('available_functions:', json.dumps([(f['n'], f['a']) for f in dd['available_functions']]), flush=True)
open(r'D:\scan\netlify_report\_last_did2.txt', 'w').write(DID)
print('DEPLOY DONE DID:', DID, flush=True)
