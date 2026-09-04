# -*- coding: utf-8 -*-
# _idn_userconf.py - check user confirmation state + try mgmt PUT to confirm + set password
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'
UID1 = 'eda80a6a-92b6-4f2d-98c5-ad71664b6dc6'  # signup-created (unconfirmed, has confirmation_sent_at)
UID2 = '81a002fe-26a5-4033-af27-fa5559fcace5'  # mgmt-created
EMAIL2 = 'zztest-idn-0942@qq.com'
PW = 'ZzTest!2345qa'

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {'Authorization': 'Bearer ' + tok}
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.headers.get('content-type',''), resp.read(3000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(3000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)
print('=== user details (confirm state) ===')
for uid in (UID1, UID2):
    st, ct, b = req('GET', base + '/users/%s' % uid, tok=TOKEN_A)
    print(uid[:8], st, b[:600].replace('\n', ' '))

print()
print('=== mgmt PUT /users/{uid} variants (confirm + password) ===')
for bd in (
    {'email_confirm': True, 'password': PW},
    {'confirmed_at': '2026-09-02T09:59:00Z', 'password': PW},
    {'email_confirm': True, 'password': PW, 'user_metadata': {'t': 1}},
):
    st, ct, b = req('PUT', base + '/users/%s' % UID2, bd, tok=TOKEN_A)
    print('body=%s' % json.dumps(bd)[:100])
    print('  -> %s %s' % (st, b[:600].replace('\n', ' ')))
    if st in (200, 201):
        break
