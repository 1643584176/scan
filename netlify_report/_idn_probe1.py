# -*- coding: utf-8 -*-
# _idn_probe1.py - probe identity-instances routes with TOKEN_A (read-only + OPTIONS first)
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {}
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    if body is not None: hdrs['Content-Type'] = ct
    data = None if body is None else (json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode())
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=20)
        return resp.status, resp.headers.get('content-type',''), resp.read(1000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(1000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

base = 'https://api.netlify.com/api/v1'
paths = [
    ('GET',  '/sites/%s/identity/instances' % SITE_A, None),
    ('GET',  '/sites/%s/identity/instance' % SITE_A, None),
    ('GET',  '/sites/%s/identity' % SITE_A, None),
    ('POST', '/sites/%s/identity/instances' % SITE_A, {}),
    ('OPTIONS', '/sites/%s/identity/instances' % SITE_A, None),
]
for m, p, b in paths:
    st, ct, body = req(m, base + p, b, tok=TOKEN_A)
    print('== %s %s' % (m, p))
    print('   %s %s %s' % (st, ct, body[:400].replace('\n', ' ')))
