# -*- coding: utf-8 -*-
"""probe4 重部署:create -> state=uploading -> fn -> html -> publish"""
import http.client, ssl, json, sys, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B
ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs=''):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_B, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

with open(r'D:\scan\netlify_report\_zisi\out2\probe4.zip', 'rb') as f:
    fzip = f.read()
html = b'<html><body>p4</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
functions = {'probe4': hashlib.sha256(fzip).hexdigest()}

s, raw = api('/api/v1/sites/%s/deploys' % SITE_B, method='POST',
             body={'title': 'fn-p4d', 'files': files, 'functions': functions})
print('create:', s, raw[:120].decode('utf-8', 'replace'))
d = json.loads(raw)
DID = d.get('id')
print('DID:', DID, 'state:', d.get('state'))
if s != 200:
    sys.exit(1)

# 尝试状态流转:new -> uploading
for st_name in ['uploading']:
    s1, raw1 = api('/api/v1/sites/%s/deploys/%s' % (SITE_B, DID), method='PUT', body={'state': st_name})
    print('PUT state %s: %d %s' % (st_name, s1, raw1[:150].decode('utf-8', 'replace').replace('\n', ' ')))

# 查状态
s2, raw2 = api('/api/v1/deploys/%s' % DID)
d2 = json.loads(raw2) if s2 == 200 else {}
print('state now:', d2.get('state'), '| required:', str(d2.get('required'))[:100])

# fn PUT
for i in range(8):
    s3, raw3 = api('/api/v1/deploys/%s/functions/probe4' % DID, method='PUT', raw_body=fzip,
                   ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
    print('PUT fn try%d: %d %s' % (i, s3, raw3[:150].decode('utf-8', 'replace').replace('\n', ' ')))
    if s3 == 200:
        break
    time.sleep(1.0)
