# -*- coding: utf-8 -*-
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

html = b'<html><body>p4</body></html>'
files = {'/index.html': hashlib.sha1(html).hexdigest()}
body = {'title': 'fn-p4b', 'files': files, 'functions': {}}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_B, method='POST', body=body)
print('create:', s, raw[:200].decode('utf-8', 'replace'))
d = json.loads(raw)
DID = d.get('id')
print('DID:', DID, 'state:', d.get('state'))

s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=html,
             ctype='application/octet-stream', qs='?size=%d' % len(html))
print('put html FULL:', s, raw[:400].decode('utf-8', 'replace'))
