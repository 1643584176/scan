# -*- coding: utf-8 -*-
# _idn_cleanup.py - double-slash admin/users check + full cleanup of identity test users + instance
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
        return resp.status, resp.headers.get('content-type',''), resp.read(1500).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(1500).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

print('=== 1. double-slash bypass on admin paths (no token) ===')
for p in ('/.netlify//identity/admin/users', '/.netlify//identity/admin/settings',
          '/.netlify//identity/user', '/.netlify//identity/signup'):
    st, ct, b = req('GET', 'https://sec-test-rcf6lz.netlify.app' + p)
    print('%-40s -> %s %s %s' % (p, st, ct[:22], b[:100].replace('\n',' ')))

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)

print()
print('=== 2. list & delete all test users ===')
st, ct, b = req('GET', base + '/users', tok=TOKEN_A)
users = json.loads(b) if st == 200 else []
print('users found:', len(users))
for u in users:
    st2, _, _ = req('DELETE', base + '/users/%s' % u['id'], tok=TOKEN_A)
    print('  delete %s (%s) -> %s' % (u['email'], u['id'][:8], st2))

print()
print('=== 3. cleanup instance (disable identity; reversible via POST /sites/{id}/identity) ===')
st, ct, b = req('DELETE', base, tok=TOKEN_A)
print('DELETE instance ->', st, ct, b[:200].replace('\n',' '))
st2, ct2, b2 = req('GET', base, tok=TOKEN_A)
print('GET after ->', st2, ct2, b2[:150].replace('\n',' '))
