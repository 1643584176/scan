# -*- coding: utf-8 -*-
"""Netlify:部署 probe1+probe2+probe3(zip-it-and-ship-it 标准产物)"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', timeout=20):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
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
for name in ('probe1', 'probe2', 'probe3', 'probe4', 'probe5', 'probe6', 'probe7'):
    with open(r'D:\scan\netlify_report\_zisi\out2\%s.zip' % name, 'rb') as f:
        zips[name] = f.read()
    print(name, 'zip bytes:', len(zips[name]))

html = b'<html><body>p3</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
functions = {name: hashlib.sha256(z).hexdigest() for name, z in zips.items()}

body = {'title': 'fn-p7', 'files': files, 'functions': functions}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body=body)
d = json.loads(raw)
DID = d.get('id')
print('create:', s, 'DID:', DID, 'state:', d.get('state'), '| required_functions:', json.dumps(d.get('required_functions'))[:150])

s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html,
             ctype='application/octet-stream', qs='?size=%d' % len(html))
print('put file:', s)

done = {}
for name, fzip in zips.items():
    print('  PUT fn %s start...' % name, flush=True)
    for i in range(8):
        s2, raw2 = api('/api/v1/deploys/%s/functions/%s' % (DID, name), method='PUT', raw_body=fzip,
                       ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        if s2 == 200:
            print('PUT fn %s OK' % name)
            done[name] = True
            break
        print('  PUT %s try%d: %d %s' % (name, i, s2, raw2[:120].decode('utf-8', 'ignore').replace('\n', ' ')))
        time.sleep(0.5)

s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
dd = json.loads(raw) if s == 200 else {}
print('publish:', s, 'state:', dd.get('state'))
if dd.get('available_functions'):
    print('available_functions:', json.dumps([(f['n'], f['a'], f['r'], f['rg']) for f in dd['available_functions']]))
open(r'D:\scan\netlify_report\_last_did.txt', 'w').write(DID)
print('DID saved:', DID)
print('DEPLOY DONE')
