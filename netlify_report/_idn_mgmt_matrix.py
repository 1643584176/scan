# -*- coding: utf-8 -*-
# _idn_mgmt_matrix.py - blackbox matrix on Netlify identity mgmt service (api.netlify.com)
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, COOKIE_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
UID = '81a002fe-26a5-4033-af27-fa5559fcace5'
EMAIL2 = 'zztest-idn-0942@qq.com'

def req(method, url, body=None, tok=None, cookie=None, ct='application/json'):
    hdrs = {}
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    if cookie: hdrs['Cookie'] = cookie
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
        return resp.status, resp.headers.get('content-type',''), resp.read(1500).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(1500).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)

print('=== 1. audit with cookie vs token ===')
for nm, kw in (('cookie', COOKIE_A), ('token', TOKEN_A)):
    st, ct, b = req('GET', base + '/audit', cookie=kw if nm == 'cookie' else None,
                    tok=kw if nm == 'token' else None)
    print('audit %s -> %s %s %s' % (nm, st, ct[:25], b[:200].replace('\n',' ')))

print()
print('=== 2. users list param handling ===')
for q in ('?page=1&per_page=5', '?filter=zztest', "?filter='", '?per_page=-1', '?page=999999', '?sort=email',
          '?page=abc', '?per_page=abc'):
    st, ct, b = req('GET', base + '/users' + q, tok=TOKEN_A)
    print('%-22s -> %s %s' % (q, st, b[:200].replace('\n',' ')))

print()
print('=== 3. DELETE user semantics ===')
st, ct, b = req('DELETE', base + '/users/%s' % UID, tok=TOKEN_A)
print('DELETE ->', st, ct, b[:200].replace('\n',' '))
st, ct, b = req('GET', base + '/users/%s' % UID, tok=TOKEN_A)
print('GET after delete ->', st, b[:200].replace('\n',' '))
st, ct, b = req('POST', base + '/users', {'email': EMAIL2, 'password': 'ZzTest!2345qa'}, tok=TOKEN_A)
print('recreate same email ->', st, b[:300].replace('\n',' '))

print()
print('=== 4. method matrix on other sub-resources ===')
for p, m, bd in (
    ('/users', 'PATCH', {'email': EMAIL2}),
    ('/users', 'OPTIONS', None),
    ('/users', 'DELETE', None),
    ('/invitations', 'GET', None),
    ('/users/invite', 'GET', None),
    ('/users/invite', 'DELETE', None),
    ('/users/invite', 'PUT', {'email': 'x@qq.com'}),
):
    st, ct, b = req(m, base + p, bd, tok=TOKEN_A)
    print('%-5s %-20s -> %s %s %s' % (m, p, st, ct[:22], b[:150].replace('\n',' ')))
