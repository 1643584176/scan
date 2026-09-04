# -*- coding: utf-8 -*-
"""Data API 收尾:注入矩阵 + rpc 行为 + 错误直透面(零残留)"""
import http.client, ssl, json, sys, os, time, psycopg, urllib.parse

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'

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

print('=== 建表 ===')
print(dbq("DROP TABLE IF EXISTS public.k_datest3"))
print(dbq("CREATE TABLE public.k_datest3 (id serial PRIMARY KEY, note text, secret text, num int)"))
print(dbq("GRANT SELECT, INSERT, UPDATE, DELETE ON public.k_datest3 TO authenticated"))
print(dbq("GRANT USAGE ON SEQUENCE public.k_datest3_id_seq TO authenticated"))
print(dbq("INSERT INTO public.k_datest3 (note, secret, num) VALUES ('hello', 's3cret1', 1), ('world', 's3cret2', 2)"))

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
time.sleep(4)  # 等 schema 缓存

def da(method, path, body=None, headers=None):
    return req(DA_HOST, method, DA_BASE + path, body=body, token=jwt, headers=headers)

print('\n=== 注入矩阵 ===')
injs = [
    ('filter 单引号', '/k_datest3?note=eq.%27%27%20OR%201%3D1--'),
    ('filter 注释', '/k_datest3?note=eq.x%27--'),
    ('select 注入', '/k_datest3?select=note,secret%20FROM%20pg_authid--'),
    ('order 注入', '/k_datest3?order=num%3B%20SELECT%20pg_sleep(5)--'),
    ('limit 注入', '/k_datest3?limit=1%3BSELECT%201--'),
    ('column 不存在 hint', '/k_datest3?select=note,zzz'),
    ('函数 select', '/k_datest3?select=note,count(*)'),
    ('cast 注入', "/k_datest3?num=eq.1::text"),
    ('json 过滤', "/k_datest3?note=in.(%22x%22,hello)"),
]
for tag, p in injs:
    st, raw = da('GET', p)
    print('  [%s] -> %d %s' % (tag, st, raw.decode(errors='replace')[:140]))
    time.sleep(0.3)

print('\n=== rpc 行为 ===')
for fn, body in [('k_datest3', {}), ('nonexistent_fn', {}), ('version', {}), ('current_database', {})]:
    st, raw = da('POST', '/rpc/' + fn, body)
    print('  rpc %s -> %d %s' % (fn, st, raw.decode(errors='replace')[:150]))
    time.sleep(0.3)

print('\n=== 错误直透(表不存在信息) ===')
for t in ('zz_not_exist', 'user', 'users_sync'):
    st, raw = da('GET', '/' + t + '?limit=1')
    print('  /%s -> %d %s' % (t, st, raw.decode(errors='replace')[:150]))

print('\n=== 方法变体(HEAD/OPTIONS/PUT) ===')
for m in ('HEAD', 'OPTIONS', 'PUT'):
    st, raw = da(m, '/k_datest3')
    print('  %s -> %d %s' % (m, st, raw.decode(errors='replace')[:120]))

print('\n=== 清理 ===')
print(dbq("DROP TABLE IF EXISTS public.k_datest3"))
print(dbq("SELECT nspname||'.'||relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE relname LIKE 'k_datest%%'"))
dbc.close()
