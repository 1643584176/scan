# -*- coding: utf-8 -*-
"""PG neon_auth 表深挖 + neonauth better-auth 端点探测"""
import psycopg, http.client, ssl, json, time
ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'

conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return [('ERR', str(e)[:150])]

print('[1] project_config:', q('SELECT * FROM neon_auth.project_config'), flush=True)
print('[2] jwks rows:', q('SELECT count(*) FROM neon_auth.jwks'), flush=True)
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='neon_auth' AND table_name='jwks'")
print('[3] jwks cols:', cur.fetchall(), flush=True)
print('[4] user cols:', q("SELECT column_name FROM information_schema.columns WHERE table_schema='neon_auth' AND table_name='user'"), flush=True)
print('[5] session cols:', q("SELECT column_name FROM information_schema.columns WHERE table_schema='neon_auth' AND table_name='session'"), flush=True)
print('[6] policies:', q("SELECT tablename, policyname, cmd, roles FROM pg_policies WHERE schemaname='neon_auth'"), flush=True)
print('[7] neon_auth role:', q("SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication FROM pg_roles WHERE rolname='neon_auth'"), flush=True)
print('[8] neon_auth members:', q("SELECT m.rolname AS member_of, g.rolname AS grantor_chain FROM pg_auth_members am JOIN pg_roles m ON m.oid=am.member JOIN pg_roles g ON g.oid=am.roleid WHERE m.rolname='neon_auth' OR g.rolname='neon_auth'"), flush=True)
print('[9] neon_auth table owners:', q("SELECT tablename, tableowner FROM pg_tables WHERE schemaname='neon_auth' ORDER BY 1"), flush=True)
print('[10] RLS on user:', q("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='neon_auth' AND relkind='r'"), flush=True)
conn.close()

# better-auth 端点探测
def na_get(path, method='GET', body=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        conn.request(method, path, body=json.dumps(body).encode() if body else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw[:300]
    except Exception as e:
        return 0, str(e).encode()[:150]

print('\n== better-auth endpoint probe ==', flush=True)
for p in ['/neondb/auth/get-session', '/neondb/auth/sign-up/email', '/neondb/auth/sign-in/email',
          '/neondb/auth/list-sessions', '/neondb/auth/delete-user', '/neondb/auth/error',
          '/api/auth/get-session', '/neondb/auth/magic-link/send', '/neondb/auth/forget-password']:
    st, raw = na_get(p)
    print('[GET %s] -> %d | %s' % (p, st, raw.decode(errors='replace')[:160]), flush=True)
    time.sleep(0.6)
# sign-up POST 试探(看是否开放注册,不发真实注册)
for p in ['/neondb/auth/sign-up/email', '/neondb/auth/sign-in/email']:
    st, raw = na_get(p, 'POST', {'email': 'test@example.com', 'password': 'x'})
    print('[POST %s] -> %d | %s' % (p, st, raw.decode(errors='replace')[:200]), flush=True)
    time.sleep(0.6)
