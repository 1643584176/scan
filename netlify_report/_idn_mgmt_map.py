# -*- coding: utf-8 -*-
# _idn_mgmt_map.py - map identity management sub-resources on api.netlify.com (read-only)
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
FAKE_INST = '000000000000000000000000'
FAKE_SITE = '00f00000-0000-4000-8000-000000000000'

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {'Authorization': 'Bearer ' + tok}
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=20)
        return resp.status, resp.headers.get('content-type',''), resp.read(2000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(2000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

def show(m, p, tok=TOKEN_A, b=None):
    st, ct, body = req(m, 'https://api.netlify.com' + p, body=b, tok=tok)
    kind = ct.split(';')[0]
    print('%-6s %-110s -> %s %s' % (m, p, st, kind))
    if st in (200, 201) or kind == 'application/json':
        print('      %s' % body[:500].replace('\n', ' '))
    return st, ct, body

print('--- site field changes after identity enable ---')
st, ct, b = req('GET', 'https://api.netlify.com/api/v1/sites/%s' % SITE_A, tok=TOKEN_A)
try:
    j = json.loads(b)
    for k in ('identity_instance_id', 'identity_id', 'jwt_secret', 'id_domain', 'name', 'capabilities'):
        print('  %s = %s' % (k, j.get(k)))
    if isinstance(j.get('capabilities'), dict):
        print('  capabilities keys:', list(j['capabilities'].keys()))
except Exception as e:
    print('  parse err', e, b[:300])

print()
print('--- identity mgmt endpoints (real inst vs fake inst vs fake site) ---')
paths = [
    '/api/v1/sites/%s/identity/%s' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/users' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/users?page=1&per_page=10' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/config' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/tokens' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/settings' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/users/invite' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s/emails' % (SITE_A, INST),
    '/api/v1/sites/%s/identity/%s' % (SITE_A, FAKE_INST),
    '/api/v1/sites/%s/identity/%s/users' % (SITE_A, FAKE_INST),
    '/api/v1/sites/%s/identity/%s/users' % (FAKE_SITE, INST),
]
for p in paths:
    show('GET', p)
