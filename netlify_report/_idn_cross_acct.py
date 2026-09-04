# -*- coding: utf-8 -*-
# _idn_cross_acct.py - cross-account matrix: TOKEN_B against SITE_A identity instance
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

INST_A = '6a97f260e3e0091b16d132ce'  # identity instance on SITE_A (team A)
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
        return resp.status, resp.headers.get('content-type',''), resp.read(4000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(4000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

def show(m, p, tok, b=None):
    st, ct, body = req(m, 'https://api.netlify.com' + p, body=b, tok=tok)
    print('%-5s %-46s tok=%s -> %s' % (m, p, 'A' if tok == TOKEN_A else 'B', st))
    if st in (200, 201) or 'json' in ct:
        print('      %s' % body[:800].replace('\n', ' '))
    return st, ct, body

base = '/api/v1/sites/%s/identity/%s' % (SITE_A, INST_A)
print('=== cross-account: B token on A instance ===')
for p in (base, base + '/users'):
    show('GET', p, TOKEN_B)

print('=== control: A token (same) ===')
for p in (base, base + '/users'):
    show('GET', p, TOKEN_A)

print('=== B token, site_id variants ===')
show('GET', '/api/v1/sites/%s/identity/%s/users' % (SITE_B, INST_A), TOKEN_B)
show('GET', '/api/v1/sites/%s/identity/%s/users' % (FAKE_SITE, INST_A), TOKEN_B)

print('=== B token writes on A instance (reversible: invite only) ===')
# invite uses user_id uuid per earlier 500 hint; send random uuid to learn semantics
show('POST', base + '/users/invite', TOKEN_B, {'user_id': '00000000-0000-4000-8000-000000000001'})
