# -*- coding: utf-8 -*-
# _idn_login.py - solve /token grant and get user JWT for created user
import json, urllib.request, urllib.error

HOST = 'https://sec-test-rcf6lz.netlify.app/.netlify/identity'
EMAIL = 'zztest-idn-0942@qq.com'
PW = 'ZzTest!2345qa'

def raw_req(method, url, data_bytes, hdrs):
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data_bytes)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.read(2000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', str(e)[:200]

print('=== 1. JSON grant_type=password (created user) ===')
st, b = raw_req('POST', HOST + '/token',
                json.dumps({'grant_type': 'password', 'email': EMAIL, 'password': PW}).encode(),
                {'Content-Type': 'application/json'})
print(st, b[:500].replace('\n', ' '))

print()
print('=== 2. urlencoded grant_type=password ===')
st, b = raw_req('POST', HOST + '/token',
                ('grant_type=password&email=%s&password=%s' % (EMAIL, PW)).encode(),
                {'Content-Type': 'application/x-www-form-urlencoded'})
print(st, b[:500].replace('\n', ' '))

print()
print('=== 3. JSON refresh_token grant (learn valid grants) ===')
st, b = raw_req('POST', HOST + '/token',
                json.dumps({'grant_type': 'refresh_token', 'refresh_token': 'x'}).encode(),
                {'Content-Type': 'application/json'})
print(st, b[:500].replace('\n', ' '))

print()
print('=== 4. JSON otp grant (learn) ===')
st, b = raw_req('POST', HOST + '/token',
                json.dumps({'grant_type': 'otp', 'email': EMAIL}).encode(),
                {'Content-Type': 'application/json'})
print(st, b[:500].replace('\n', ' '))
