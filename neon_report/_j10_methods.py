# -*- coding: utf-8 -*-
"""Data API 修正重测:配置确认 + GRANT 后方法集 + Accept-Profile 跨 schema"""
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

print('=== 当前 data-api 配置 ===')
st, body = ctl_req('GET', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (PID, BID))
print('%d | %s' % (st, body[:500]))

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

# 建表 + GRANT(模拟应用正常授权)
print('\n=== 建表 + GRANT authenticated ===')
print(dbq("DROP TABLE IF EXISTS public.k_datest2"))
print(dbq("CREATE TABLE public.k_datest2 (id serial PRIMARY KEY, note text, secret text)"))
print(dbq("GRANT SELECT, INSERT, UPDATE, DELETE ON public.k_datest2 TO authenticated"))
print(dbq("GRANT USAGE ON SEQUENCE public.k_datest2_id_seq TO authenticated"))
print(dbq("INSERT INTO public.k_datest2 (note, secret) VALUES ('hello', 's3cret1')"))
time.sleep(5)  # 等 schema 缓存刷新

print('\n=== 方法集(authenticated + GRANT 后) ===')
st, raw = da('GET', '/k_datest2')
print('GET -> %d %s' % (st, raw.decode(errors='replace')[:250]))
st, raw = da('POST', '/k_datest2', {'note': 'inj', 'secret': 'x'})
print('POST -> %d %s' % (st, raw.decode(errors='replace')[:250]))
st, raw = da('PATCH', '/k_datest2?note=eq.inj', {'note': 'inj2'})
print('PATCH -> %d %s' % (st, raw.decode(errors='replace')[:250]))
st, raw = da('DELETE', '/k_datest2?note=eq.inj2')
print('DELETE -> %d %s' % (st, raw.decode(errors='replace')[:250]))

print('\n=== Accept-Profile 跨 schema ===')
st, raw = da('GET', '/users?limit=2', headers={'Accept-Profile': 'auth'})
print('auth/users -> %d %s' % (st, raw.decode(errors='replace')[:200]))
st, raw = da('GET', '/users_sync?limit=2', headers={'Accept-Profile': 'neon_auth'})
print('neon_auth/users_sync -> %d %s' % (st, raw.decode(errors='replace')[:200]))
st, raw = da('GET', '/users?limit=2', headers={'Accept-Profile': 'neon_auth'})
print('neon_auth/users -> %d %s' % (st, raw.decode(errors='replace')[:200]))

print('\n=== RPC 面 ===')
st, raw = da('POST', '/rpc/k_datest2', {})
print('rpc nonexistent -> %d %s' % (st, raw.decode(errors='replace')[:150]))

print('\n=== 清理 ===')
print(dbq("DROP TABLE IF EXISTS public.k_datest2"))
print(dbq("SELECT nspname||'.'||relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE relname LIKE 'k_datest%%'"))
dbc.close()
