# -*- coding: utf-8 -*-
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B
ctx = ssl.create_default_context()
SITE = 'd2977de0-d24d-4544-81cb-933e610cad7d'

def api(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Authorization': 'Bearer ' + TOKEN_B}
    if body is not None:
        h['Content-Type'] = 'application/json'
    conn.request(method, path, body=json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close(); return r.status, raw

s, raw = api('/api/v1/sites/%s' % SITE)
print('site:', s)
d = json.loads(raw)
print('name:', d.get('name'), '| url:', d.get('url'))
print('repo:', json.dumps(d.get('repository'), indent=1)[:600])
print('build_settings:', json.dumps(d.get('build_settings'), indent=1)[:600])
s2, raw2 = api('/api/v1/sites/%s/build_hooks' % SITE)
print('build_hooks:', s2, raw2[:500].decode('utf-8', 'replace'))
