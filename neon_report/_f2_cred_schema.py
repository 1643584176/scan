# -*- coding: utf-8 -*-
"""dump credentials 相关 schema + 当前 credentials 列表"""
import json, http.client, ssl, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
s = d['components']['schemas']
for t in ('CredentialScope', 'GrantedCredentialScope', 'CreateCredentialRequest',
          'CreateCredentialResponse', 'CredentialSecret', 'RotateCredentialResponse',
          'CredentialMeta', 'ListCredentialsResponse'):
    if t in s:
        print('=' * 20, t)
        print(json.dumps(s[t], indent=1)[:1800])
    else:
        print('=' * 20, t, 'NOT FOUND')

# 当前列表
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
     'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
h.update(HEADERS_TEST)
c = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
c.request('GET', API_BASE + '/projects/orange-sun-90493739/branches/br-wandering-field-w2ob6mpn/credentials', headers=h)
r = c.getresponse(); raw = r.read(); c.close()
print('=' * 20, 'current list -> %d' % r.status)
print(raw.decode(errors='replace')[:1200])
