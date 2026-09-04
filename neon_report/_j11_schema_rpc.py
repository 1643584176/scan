# -*- coding: utf-8 -*-
"""Data API: PATCH 3schema + Accept/Content-Profile + rpc 深测(测完恢复)"""
import http.client, ssl, json, sys, os, re, time, html, psycopg

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

print('=== PATCH db_schemas=[public,auth,neon_auth] ===')
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public', 'auth', 'neon_auth']}})
print('-> %d %s' % (st, body[:200]))
time.sleep(3)

print('\n=== Accept-Profile / Content-Profile ===')
for prof, path in [('auth', '/users?limit=2'), ('auth', '/sessions?limit=2'), ('neon_auth', '/users_sync?limit=2')]:
    st, raw = da('GET', path, headers={'Accept-Profile': prof})
    print('  [%s] GET %s -> %d %s' % (prof, path, st, raw.decode(errors='replace')[:200]))
st, raw = da('GET', '/users?limit=2', headers={'Accept-Profile': 'auth,public'})
print('  multi-profile -> %d %s' % (st, raw.decode(errors='replace')[:150]))

print('\n=== schema 探测(枚举 auth/neon_auth 表名) ===')
for t in ('users', 'sessions', 'accounts', 'verification_tokens', 'users_sync', 'organizations', 'members'):
    st, raw = da('GET', '/' + t + '?limit=1', headers={'Accept-Profile': 'auth'})
    if st != 404 or 'public.' not in raw.decode(errors='replace'):
        print('  auth/%s -> %d %s' % (t, st, raw.decode(errors='replace')[:120]))
    st2, raw2 = da('GET', '/' + t + '?limit=1', headers={'Accept-Profile': 'neon_auth'})
    if st2 != 404 or 'public.' not in raw2.decode(errors='replace'):
        print('  neon_auth/%s -> %d %s' % (t, st2, raw2.decode(errors='replace')[:120]))

print('\n=== rpc 深测 ===')
# 先查 neondb public 有哪些函数
import psycopg
PG_PWD = 'npg_cI5ynlaAqjU2'
PG_HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
dbc = psycopg.connect('postgresql://neondb_owner:%s@%s/neondb' % (PG_PWD, PG_HOST), connect_timeout=20)
dbc.autocommit = True
dcur = dbc.cursor()
dcur.execute("SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','auth','neon_auth') ORDER BY 1,2")
for r in dcur.fetchall():
    print('  fn: %s.%s(%s)' % (r[0], r[1], r[2]))
dbc.close()

print('\n=== 恢复 db_schemas=[public] ===')
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public']}})
print('restore -> %d %s' % (st, body[:150]))
