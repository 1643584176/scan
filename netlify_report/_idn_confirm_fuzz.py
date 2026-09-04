# -*- coding: utf-8 -*-
# _idn_confirm_fuzz.py - find working fields to confirm user + set password; hunt generate_link
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
UID = '81a002fe-26a5-4033-af27-fa5559fcace5'
EMAIL = 'zztest-idn-0942@qq.com'
PW = 'ZzTest!2345qa'
HOST = 'https://sec-test-rcf6lz.netlify.app/.netlify/identity'

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
        return resp.status, resp.read(2000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', str(e)[:150]

def pwlogin(email, pw):
    st, b = req('POST', HOST + '/token',
                ('grant_type=password&email=%s&password=%s' % (email, pw)).encode(),
                ct='application/x-www-form-urlencoded')
    return st, b

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)

print('=== 1. confirm-field name fuzz via PUT (recheck GET after each) ===')
for field in ('email_confirm', 'confirm', 'confirmed', 'auto_confirm', 'email_confirmed', 'is_confirmed', 'confirmed_at'):
    body = {field: True if field != 'confirmed_at' else '2026-09-02T10:05:00Z'}
    st, _ = req('PUT', base + '/users/%s' % UID, body, tok=TOKEN_A)
    st2, b2 = req('GET', base + '/users/%s' % UID, tok=TOKEN_A)
    has_conf = 'confirmed_at' in b2 or 'confirmation_sent_at' not in b2
    mark = 'CONFIRMED?' if ('"confirmed_at"' in b2) else ''
    print('  %-16s -> PUT %s | GET%s %s' % (field, st, st2, mark))

print()
print('=== 2. password field effect (PUT then login) ===')
st, _ = req('PUT', base + '/users/%s' % UID, {'password': PW}, tok=TOKEN_A)
st2, b2 = pwlogin(EMAIL, PW)
print('  PUT password -> %s, login -> %s %s' % (st, st2, b2[:150].replace('\n',' ')))

print()
print('=== 3. hunt generate_link-like mgmt endpoints (POST, safe-ish: would send email at most) ===')
for p in ('/users/%s/generate_link' % UID, '/users/%s/recovery_link' % UID,
          '/users/generate_link', '/generate_link', '/users/%s/confirm' % UID,
          '/users/%s/verify' % UID, '/users/%s/resend' % UID, '/users/%s/password' % UID):
    st, b = req('POST', base + p, {'type': 'confirmation', 'email': EMAIL}, tok=TOKEN_A)
    print('  POST %-45s -> %s %s' % (p.split('/')[-1], st, b[:180].replace('\n',' ')))
