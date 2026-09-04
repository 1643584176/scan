# -*- coding: utf-8 -*-
"""neon_auth 表实测(authenticated 视角):读/写权限 + 结构 + 恢复"""
import http.client, ssl, json, sys, os, re, time, html

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

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

def ctl_req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    body0 = r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    txt = body0.decode('utf-8', 'replace')
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn = http.client.HTTPSConnection(API_HOST, timeout=25)
    hdrs = {'Cookie': '; '.join(parts), 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

# PATCH 3 schema
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public', 'neon_auth', 'auth']}})
print('PATCH -> %d' % st)
time.sleep(3)

# 登录
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'}
conn.request('POST', '/neondb/auth/sign-in/email', body=json.dumps({'email': EMAIL, 'password': PWD}).encode(), headers=h)
r = conn.getresponse(); r.read()
cks = r.headers.get_all('Set-Cookie')
conn.close()
cookie_all = '; '.join(c.split(';')[0] for c in cks)
st, raw = req(NA, 'GET', '/neondb/auth/token', cookie=cookie_all)
jwt = json.loads(raw).get('token', '')

def da(method, path, body=None, headers=None):
    return req(DA_HOST, method, DA_BASE + path, body=body, token=jwt, headers=headers)

H = {'Accept-Profile': 'neon_auth'}
print('\n=== neon_auth 表读(authenticated) ===')
for t in ('user', 'session', 'account', 'verification', 'organization', 'member'):
    st, raw = da('GET', '/' + t + '?limit=3', headers=H)
    print('  GET /%s -> %d %s' % (t, st, raw.decode(errors='replace')[:250]))
    time.sleep(0.3)

print('\n=== neon_auth 表写尝试(只试无害值,即时回滚语义=无事务,试 insert 失败即停) ===')
st, raw = da('POST', '/user', {'email': 'x@x.com'}, headers=H)
print('  POST /user -> %d %s' % (st, raw.decode(errors='replace')[:200]))

print('\n=== OpenAPI(3schema 状态) ===')
st, raw = da('GET', '/', headers={'Accept': 'application/openapi+json'})
print('openapi -> %d %s' % (st, raw.decode(errors='replace')[:400]))

# 恢复
print('\n=== 恢复 ===')
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public']}})
print('restore -> %d %s' % (st, body[:150]))
