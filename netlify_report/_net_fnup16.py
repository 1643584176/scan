# -*- coding: utf-8 -*-
"""Netlify:账号 B 站点部署全部 probe1-7(zip-it-and-ship-it 产物)"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
DOMAIN_B = 'sec-b-08v4pk.netlify.app'
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

zips = {}
for name in ('probe1', 'probe2', 'probe3', 'probe4', 'probe5', 'probe6', 'probe7', 'probe8', 'probe9'):
    with open(r'D:\scan\netlify_report\_zisi\out2\%s.zip' % name, 'rb') as f:
        zips[name] = f.read()
    print(name, 'zip bytes:', len(zips[name]), flush=True)

html = b'<html><body>siteB</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
functions = {name: hashlib.sha256(z).hexdigest() for name, z in zips.items()}

body = {'title': 'fn-all9', 'files': files, 'functions': functions}
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

done = {}
for name, fzip in zips.items():
    print('  PUT fn %s start...' % name, flush=True)
    for i in range(8):
        s2, raw2 = api('/api/v1/deploys/%s/functions/%s' % (DID, name), method='PUT', raw_body=fzip,
                       ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        if s2 == 200:
            print('PUT fn %s OK' % name, flush=True)
            done[name] = True
            break
        print('  PUT %s try%d: %d %s' % (name, i, s2, raw2[:100].decode('utf-8', 'ignore').replace('\n', ' ')), flush=True)
        time.sleep(0.4)

s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_B, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'), flush=True)
if dd.get('available_functions'):
    print('available_functions:', json.dumps([(f['n'], f['a'], f['r']) for f in dd['available_functions']]), flush=True)
open(r'D:\scan\netlify_report\_last_did.txt', 'w').write(DID)
print('DEPLOY DONE DID:', DID, flush=True)
