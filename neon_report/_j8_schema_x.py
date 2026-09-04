# -*- coding: utf-8 -*-
"""Data API: openapi 全量 + schema 跨暴露(PATCH db_schemas 测试, 测完恢复)"""
import http.client, ssl, json, base64, sys, os

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'
ctx_data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID = ctx_data['pid']
BID = ctx_data['bid']

def req(host, method, path, body=None, token=None, headers=None, cookie=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    if token:
        h['Authorization'] = 'Bearer ' + token
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

# 登录拿 JWT(完整登录拿 cookie 再换 JWT)
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'}
conn.request('POST', '/neondb/auth/sign-in/email', body=json.dumps({'email': EMAIL, 'password': PWD}).encode(), headers=h)
r = conn.getresponse(); r.read()
cks = r.headers.get_all('Set-Cookie')
conn.close()
cookie_all = '; '.join(c.split(';')[0] for c in cks)
st, raw = req(NA, 'GET', '/neondb/auth/token', cookie=cookie_all)
jwt = json.loads(raw).get('token', '')
print('JWT ok len=%d' % len(jwt))

def da(method, path, body=None, headers=None):
    return req(DA_HOST, method, DA_BASE + path, body=body, token=jwt, headers=headers)

print('\n=== OpenAPI 全量 ===')
st, raw = da('GET', '/', headers={'Accept': 'application/openapi+json'})
print('openapi -> %d len=%d' % (st, len(raw)))
try:
    spec = json.loads(raw)
    print('paths:')
    for k in sorted(spec.get('paths', {})):
        print('  %s' % k)
except Exception as e:
    print(raw.decode(errors='replace')[:500])

print('\n=== public 表探测 ===')
for t in ('health_check', 'lakebase_attributes', 'k_evt_log', 'users'):
    st, raw = da('GET', '/%s?limit=1' % t)
    print('  /%s -> %d %s' % (t, st, raw.decode(errors='replace')[:120]))

print('\n=== PATCH db_schemas 加 auth/neon_auth(测完恢复) ===')
# 控制面 PATCH
def ctl_req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, timeout=20)
    hdrs = {'Cookie': cookie_str(), 'Content-Type': 'application/json'}
    hdrs.update(HEADERS_TEST)
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public', 'auth', 'neon_auth']}})
print('PATCH -> %d | %s' % (st, body[:400]))
time.sleep(2)
print('\n=== PATCH 后跨 schema 访问 ===')
for t in ('auth/users', 'neon_auth/users_sync', 'auth/sessions', 'auth/accounts'):
    st, raw = da('GET', '/%s?limit=1' % t)
    print('  /%s -> %d %s' % (t, st, raw.decode(errors='replace')[:150]))
st, raw = da('GET', '/', headers={'Accept': 'application/openapi+json'})
try:
    spec = json.loads(raw)
    print('openapi paths now:')
    for k in sorted(spec.get('paths', {})):
        print('  %s' % k)
except Exception:
    print(raw.decode(errors='replace')[:300])

print('\n=== 恢复 db_schemas=["public"] ===')
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public']}})
print('restore -> %d | %s' % (st, body[:200]))

import time
