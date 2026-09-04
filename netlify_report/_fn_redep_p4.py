# -*- coding: utf-8 -*-
"""重新部署 probe4 到 B site(最小 deploy)"""
import http.client, ssl, json, sys, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

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
print('probe4.zip bytes:', len(fzip))

html = b'<html><body>p4</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
functions = {'probe4': hashlib.sha256(fzip).hexdigest()}
body = {'title': 'fn-p4', 'files': files, 'functions': functions}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_B, method='POST', body=body)
print('create:', s, raw[:200].decode('utf-8', 'replace'))
if s != 200:
    sys.exit(1)
d = json.loads(raw)
DID = d.get('id')
print('DID:', DID, 'state:', d.get('state'))

s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html, ctype='application/octet-stream',
             qs='?size=%d' % len(html))
print('put html:', s)

# 等待 deploy 状态从 uploading -> processed
for i in range(30):
    s3, raw3 = api('/api/v1/deploys/%s' % DID)
    try:
        st3 = json.loads(raw3).get('state')
    except Exception:
        st3 = None
    print('poll state try%d: %s' % (i, st3))
    if st3 in ('processed', 'ready'):
        break
    time.sleep(1.0)

ok = False
for i in range(10):
    s2, raw2 = api('/api/v1/deploys/%s/functions/probe4' % DID, method='PUT', raw_body=fzip,
                   ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
    print('PUT fn try%d: %d %s' % (i, s2, raw2[:120].decode('utf-8', 'replace').replace('\n', ' ')))
    if s2 == 200:
        ok = True
        break
    time.sleep(0.5)
if not ok:
    sys.exit(1)

s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_B, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'))
if dd.get('available_functions'):
    print('available_functions:', json.dumps([(f.get('n'), f.get('a'), f.get('r')) for f in dd['available_functions']]))
print('DONE DID:', DID)
