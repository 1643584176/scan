# -*- coding: utf-8 -*-
# _idn_signup.py - probe GoTrue public surface on site domain (signup/405 detail + real POST)
import json, urllib.request, urllib.error

HOST = 'https://sec-test-rcf6lz.netlify.app'
BASE = HOST + '/.netlify/identity'

def req(method, url, body=None, ct='application/json', raw_hdr=False):
    hdrs = {}
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        hd = dict(resp.headers) if raw_hdr else {}
        return resp.status, hd, resp.read(2000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        hd = dict(e.headers) if raw_hdr else {}
        return e.code, hd, e.read(2000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', {}, str(e)[:200]

print('=== GET /signup full detail ===')
st, hd, b = req('GET', BASE + '/signup', raw_hdr=True)
print(st, b[:400].replace('\n', ' '))
for k, v in hd.items():
    if k.lower() in ('server', 'via', 'x-nf-request-id', 'x-request-id', 'content-type', 'allow'):
        print('  %s: %s' % (k, v))

print()
print('=== POST /signup (uncontrolled test email) ===')
st, hd, b = req('POST', BASE + '/signup', {'email': 'zztest-idn-0941@qq.com', 'password': 'ZzTest!2345qa'})
print(st, b[:600].replace('\n', ' '))

print()
print('=== POST /token grant_type=password (nonexistent user) ===')
st, hd, b = req('POST', BASE + '/token', {'grant_type': 'password', 'email': 'nobody@qq.com', 'password': 'x'})
print(st, b[:300].replace('\n', ' '))

print()
print('=== GET /settings (detailed) ===')
st, hd, b = req('GET', BASE + '/settings', raw_hdr=True)
print(st, b[:400].replace('\n', ' '))

print()
print('=== other endpoint method probes ===')
for m, p, body in [
    ('GET',  '/.netlify/identity', None),
    ('POST', '/.netlify/identity/recover', {'email': 'zztest-idn-0941@qq.com'}),
    ('GET',  '/.netlify/identity/user', None),
    ('GET',  '/.netlify/identity/admin', None),
    ('GET',  '/.netlify/identity/admin/settings', None),
    ('GET',  '/.netlify/identity/invite', None),
    ('GET',  '/.netlify/identity/verify', None),
    ('GET',  '/.netlify/identity/logout', None),
]:
    st, hd, b = req(m, HOST + p, body)
    print('%s %-40s -> %s %s' % (m, p, st, b[:150].replace('\n', ' ')))
