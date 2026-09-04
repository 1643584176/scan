# -*- coding: utf-8 -*-
# _idn_userops.py - mgmt user create (confirmed) then password grant login to get user JWT
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
HOST_SITE = 'https://sec-test-rcf6lz.netlify.app'
EMAIL = 'zztest-idn-0942@qq.com'
PW = 'ZzTest!2345qa'

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
        return resp.status, resp.headers.get('content-type',''), resp.read(3000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(3000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

print('=== 1. users list sync check ===')
st, ct, b = req('GET', 'https://api.netlify.com/api/v1/sites/%s/identity/%s/users' % (SITE_A, INST), tok=TOKEN_A)
print(st, b[:500].replace('\n', ' '))

print()
print('=== 2. POST /users variants (create confirmed user) ===')
base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s/users' % (SITE_A, INST)
bodies = [
    {'email': EMAIL, 'password': PW, 'email_confirm': True},
    {'email': EMAIL, 'password': PW, 'email_confirm': True, 'app_metadata': {}, 'user_metadata': {}},
    {'email': EMAIL, 'password': PW, 'confirmed_at': '2026-09-02T00:00:00Z'},
]
for bd in bodies:
    st, ct, b = req('POST', base, bd, tok=TOKEN_A)
    print('body=%s' % json.dumps(bd)[:120])
    print('  -> %s %s' % (st, b[:500].replace('\n', ' ')))
    if st in (200, 201):
        break
