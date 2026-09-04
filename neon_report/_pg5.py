# -*- coding: utf-8 -*-
"""PG 权限模型收尾:SET ROLE cloud_admin 单测 / SECURITY DEFINER 枚举 / pg_authid"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'

def fresh():
    return psycopg.connect(URI, connect_timeout=20)

# 1) SET ROLE cloud_admin 干净单测(独立连接)
c = fresh()
cur = c.cursor()
try:
    cur.execute('SET ROLE cloud_admin')
    cur.execute('SELECT current_user')
    print('[1] SET ROLE cloud_admin -> OK:', cur.fetchone())
    cur.execute('RESET ROLE')
except Exception as e:
    print('[1] SET ROLE cloud_admin -> DENIED:', str(e)[:200])
c.close()

# 2) SECURITY DEFINER 全库枚举
c = fresh()
cur = c.cursor()
cur.execute("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner) AS owner,
   pg_get_function_identity_arguments(p.oid) AS args
   FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema')
   ORDER BY 1, 2""")
rows = cur.fetchall()
print('\n[2] SECURITY DEFINER funcs (%d):' % len(rows))
for r in rows:
    print('   ', r)
c.close()

# 3) pg_authid 可读性(通常需 superuser)
c = fresh()
cur = c.cursor()
for rn in ['neondb_owner', 'anonymous', 'authenticator']:
    try:
        cur.execute('SET ROLE %s' % rn)
        cur.execute('SELECT count(*) FROM pg_authid')
        print('[3] %s read pg_authid -> %s rows' % (rn, cur.fetchone()[0]))
        cur.execute('RESET ROLE')
    except Exception as e:
        print('[3] %s read pg_authid -> DENIED: %s' % (rn, str(e)[:120]))
        try:
            cur.execute('RESET ROLE')
        except Exception:
            pass
c.close()

# 4) auth 函数可执行性(anonymous/authenticated 能否调 auth.jwt)
c = fresh()
cur = c.cursor()
for rn in ['anonymous', 'authenticated', 'authenticator']:
    for fn in ['auth.jwt()', 'auth.jwt_session_init(text)']:
        try:
            cur.execute('SET ROLE %s' % rn)
            cur.execute('SELECT has_function_privilege(%s, %s, %s)', (rn, fn, 'EXECUTE'))
            print('[4] %s exec %s -> %s' % (rn, fn, cur.fetchone()[0]))
            cur.execute('RESET ROLE')
        except Exception as e:
            print('[4] %s exec %s -> ERR %s' % (rn, fn, str(e)[:100]))
c.close()
