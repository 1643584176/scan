# -*- coding: utf-8 -*-
# _idn_surface2.py - deeper: GoTrue public surface routing + mgmt endpoint enum (read-only + safe probes)
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
UUID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_A = UUID

def req(method, url, body=None, tok=None, hdrs_extra=None, ct='application/json'):
    hdrs = dict(hdrs_extra or {})
    if tok: hdrs['Authorization'] = 'Bearer ' + tok
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=20)
        return resp.status, resp.headers.get('content-type',''), resp.read(1500).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(1500).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

print('=== A. site-domain GoTrue after enable (both hosts, common endpoints) ===')
for host in ('https://sec-test-rcf6lz.netlify.app', 'https://%s.netlify.app' % UUID):
    for p in ('/.netlify/identity/settings', '/.netlify/identity/signup', '/.netlify/identity/admin/users'):
        st, ct, b = req('GET', host + p)
        print('%-48s %s %s %s' % (host.split('//')[1] + p, st, ct[:30], b[:80].replace('\n', ' ')))

print()
print('=== B. identity.services.netlify.com tenant routing guesses (public settings) ===')
cands = [
    ('/settings', {}),
    ('/%s/settings' % UUID, {}),
    ('/%s/settings' % INST, {}),
    ('/settings', {'X-Netlify-Instance-ID': INST}),
    ('/settings', {'X-Instance-ID': INST}),
    ('/settings', {'X-GoTrue-Instance': INST}),
    ('/settings', {'X-GoTrue-Instance-ID': UUID}),
    ('/settings', {'X-Netlify-Site-ID': UUID}),
    ('/.netlify/identity/settings', {'X-GoTrue-Instance': INST}),
]
for p, hx in cands:
    st, ct, b = req('GET', 'https://identity.services.netlify.com' + p, hdrs_extra=hx)
    print('%-22s %-55s %s %s' % (str(hx)[:22], p, st, b[:100].replace('\n', ' ')))

print()
print('=== C. mgmt sub-resource GET enum (real inst, token A) ===')
subs = ['users', 'users?page=1&per_page=50', 'users/00000000-0000-4000-8000-000000000001',
        'users/count', 'invitations', 'invites', 'providers', 'oauth', 'sessions', 'password',
        'recovery', 'logs', 'activity', 'hooks', 'webhooks', 'emails/templates', 'mailer',
        'jwks', 'jwt', 'keys', 'secrets', 'roles', 'audit', 'export', 'backup']
for s in subs:
    st, ct, b = req('GET', 'https://api.netlify.com/api/v1/sites/%s/identity/%s/%s' % (SITE_A, INST, s), tok=TOKEN_A)
    if st != 404 or 'json' in ct:
        print('%-40s -> %s %s %s' % (s, st, ct[:25], b[:200].replace('\n', ' ')))
