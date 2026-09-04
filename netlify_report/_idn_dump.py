# -*- coding: utf-8 -*-
# _idn_dump.py - full identity instance config + probe identity.services.netlify.com + site .netlify/identity
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'

def req(method, url, body=None, tok=None, cookie=None, ct='application/json', hdrs_extra=None):
    hdrs = dict(hdrs_extra or {})
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    if cookie: hdrs['Cookie'] = cookie
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.headers.get('content-type',''), resp.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(6000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

print('=== 1. full identity instance via api.netlify.com ===')
for p in ('/api/v1/sites/%s/identity/instances' % SITE_A,
          '/api/v1/sites/%s/identity/%s' % (SITE_A, INST),
          '/api/v1/sites/%s/identity' % SITE_A):
    st, ct, b = req('GET', 'https://api.netlify.com' + p, tok=TOKEN_A)
    print('%s -> %s %s' % (p, st, ct))
    print(b[:3000])
    print()

print('=== 2. site .netlify/identity endpoints (now enabled) ===')
for p in ('/.netlify/identity/settings', '/.netlify/identity', '/.netlify/identity/health'):
    st, ct, b = req('GET', 'https://sec-test-rcf6lz.netlify.app' + p)
    print('%s -> %s %s %s' % (p, st, ct, b[:500].replace('\n',' ')))
    print()

print('=== 3. identity.services.netlify.com probes ===')
for p in ('/', '/health', '/settings', '/admin/users', '/.netlify/identity/settings'):
    st, ct, b = req('GET', 'https://identity.services.netlify.com' + p)
    print('%s -> %s %s %s' % (p, st, ct, b[:300].replace('\n',' ')))
    print()
