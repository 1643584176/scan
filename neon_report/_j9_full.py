# -*- coding: utf-8 -*-
"""Data API 全流程:测试表建/方法集/跨 schema 暴露/恢复清理"""
import http.client, ssl, json, base64, sys, os, re, time, html, psycopg

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'
PID = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))['pid']
BID = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))['bid']

# DB 连接(建测试表)
PG_PWD = 'npg_cI5ynlaAqjU2'
PG_HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
dbc = psycopg.connect('postgresql://neondb_owner:%s@%s/neondb' % (PG_PWD, PG_HOST), connect_timeout=20)
dbc.autocommit = True
dcur = dbc.cursor()

def dbq(sql):
    try:
        dcur.execute(sql)
        try:
            return dcur.fetchall()
        except Exception:
            return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:150]

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
    hdrs = r.headers
    conn.close()
    return st, raw, hdrs

# ---- CSRF 流程 ----
def csrf_headers():
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    body = r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    txt = body.decode('utf-8', 'replace')
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    return csrf, '; '.join(parts)

def ctl_req(method, path, body=None):
    csrf, merged = csrf_headers()
    conn = http.client.HTTPSConnection(API_HOST, timeout=25)
    hdrs = {'Cookie': merged, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, data

# ---- 建测试表 ----
print('=== 建测试表 k_datest ===')
print(dbq("DROP TABLE IF EXISTS public.k_datest"))
print(dbq("CREATE TABLE public.k_datest (id serial PRIMARY KEY, note text, secret text)"))
print(dbq("INSERT INTO public.k_datest (note, secret) VALUES ('hello', 's3cret1'), ('world', 's3cret2')"))
print(dbq("SELECT * FROM public.k_datest"))

# ---- 登录换 JWT ----
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'}
conn.request('POST', '/neondb/auth/sign-in/email', body=json.dumps({'email': EMAIL, 'password': PWD}).encode(), headers=h)
r = conn.getresponse(); r.read()
cks = r.headers.get_all('Set-Cookie')
conn.close()
cookie_all = '; '.join(c.split(';')[0] for c in cks)
st, raw, _ = req(NA, 'GET', '/neondb/auth/token', cookie=cookie_all)
jwt = json.loads(raw).get('token', '')
print('\nJWT len=%d' % len(jwt))

def da(method, path, body=None, headers=None):
    return req(DA_HOST, method, DA_BASE + path, body=body, token=jwt, headers=headers)

print('\n=== 方法集基线(authenticated) ===')
st, raw, _ = da('GET', '/k_datest')
print('GET /k_datest -> %d %s' % (st, raw.decode(errors='replace')[:300]))
st, raw, _ = da('GET', '/k_datest?select=note&note=eq.hello')
print('GET filter -> %d %s' % (st, raw.decode(errors='replace')[:200]))
st, raw, _ = da('POST', '/k_datest', {'note': 'injected', 'secret': 'x'})
print('POST -> %d %s' % (st, raw.decode(errors='replace')[:200]))
st, raw, _ = da('PATCH', '/k_datest?note=eq.injected', {'secret': 'patched'})
print('PATCH -> %d %s' % (st, raw.decode(errors='replace')[:200]))
st, raw, _ = da('DELETE', '/k_datest?note=eq.injected')
print('DELETE -> %d %s' % (st, raw.decode(errors='replace')[:200]))

print('\n=== 跨 schema PATCH ===')
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public', 'auth', 'neon_auth']}})
print('PATCH db_schemas -> %d | %s' % (st, body[:300]))
time.sleep(3)
for t in ('auth/users', 'neon_auth/users_sync', 'auth/sessions'):
    st, raw, _ = da('GET', '/%s?limit=2' % t)
    print('  /%s -> %d %s' % (t, st, raw.decode(errors='replace')[:200]))

print('\n=== 恢复配置 + 清表 ===')
st, body = ctl_req('PATCH', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID),
                   {'settings': {'db_schemas': ['public']}})
print('restore -> %d | %s' % (st, body[:200]))
print(dbq("DROP TABLE IF EXISTS public.k_datest"))
print(dbq("SELECT nspname||'.'||relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE relname LIKE 'k_%'"))
dbc.close()
