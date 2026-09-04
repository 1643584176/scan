# -*- coding: utf-8 -*-
# _idn_probe2.py - identity/instances route semantics + GraphQL introspection hunt
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, COOKIE_A, SITE_A

FAKE = '00f00000-0000-4000-8000-000000000000'

def req(method, url, body=None, tok=None, cookie=None, ct='application/json'):
    hdrs = {}
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    if cookie: hdrs['Cookie'] = cookie
    if body is not None: hdrs['Content-Type'] = ct
    data = None if body is None else (json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode())
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=20)
        return resp.status, resp.headers.get('content-type',''), resp.read(800).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(800).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

print('--- identity/instances semantics (tok A) ---')
for sid in (SITE_A, FAKE):
    st, ct, b = req('GET', 'https://api.netlify.com/api/v1/sites/%s/identity/instances' % sid, tok=TOKEN_A)
    print('%s -> %s %s %s' % (sid[:8], st, ct, b[:150]))

print('--- GraphQL endpoint hunt (cookie A) ---')
gql_urls = [
    'https://api.netlify.com/graphql',
    'https://api.netlify.com/api/v1/graphql',
    'https://app.netlify.com/graphql',
]
intro = json.dumps({'query': '{ __typename }'})
for u in gql_urls:
    st, ct, b = req('POST', u, intro, cookie=COOKIE_A)
    print('%s -> %s %s %s' % (u, st, ct, b[:200]))

print('--- candidate provision endpoints (tok A, GET only) ---')
for p in [
    '/api/v1/identity/instances',
    '/api/v1/identity-instances',
    '/api/v1/sites/%s/identity-instance' % SITE_A,
    '/api/v1/sites/%s/identity/provision' % SITE_A,
    '/api/v1/sites/%s/identity/settings' % SITE_A,
]:
    st, ct, b = req('GET', 'https://api.netlify.com' + p, tok=TOKEN_A)
    print('%s -> %s %s %s' % (p, st, ct, b[:150]))
