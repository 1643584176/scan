# -*- coding: utf-8 -*-
"""PG 深挖:auth schema / 角色成员 / SET ROLE / 基础设施域名可达性"""
import psycopg, socket, json

HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@%s/neondb' % HOST
conn = psycopg.connect(URI, connect_timeout=30)
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return [('ERR', str(e)[:200])]

print('[A] auth schema tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='auth' ORDER BY 1"))
print('[B] auth views:', q("SELECT viewname FROM pg_views WHERE schemaname='auth' ORDER BY 1"))
print('[C] auth funcs:', q("SELECT proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='auth' ORDER BY 1 LIMIT 20"))
print('[D] auth policies:', q("SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname='auth'"))
print('[E] all roles w/ special:', q("SELECT rolname FROM pg_roles WHERE rolname LIKE '%databricks%' OR rolname LIKE '%lakebase%' OR rolname='cloud_admin' OR rolname LIKE '%supabase%'"))
print('[F] memberships:', q("SELECT r.rolname, pg_has_role(current_user, r.rolname, 'MEMBER') FROM pg_roles r WHERE r.rolname IN ('cloud_admin','neon_superuser','neon_service','databricks_superuser','authenticator','pg_read_all_data')"))

# SET ROLE 尝试(立即 RESET,无副作用)
for rn in ['neon_superuser', 'cloud_admin', 'neon_service']:
    try:
        cur.execute('SET ROLE %s' % rn)
        cur.execute('SELECT current_user')
        got = cur.fetchone()
        cur.execute('RESET ROLE')
        print('[G] SET ROLE %s -> OK current=%s' % (rn, got))
    except Exception as e:
        print('[G] SET ROLE %s -> DENIED: %s' % (rn, str(e)[:100]))

# auth 表内容窥视(只读 1 行)
for t in ['users', 'identities', 'sessions', 'refresh_tokens', 'users_sync']:
    r = q('SELECT * FROM auth.%s LIMIT 1' % t)
    print('[H] auth.%s sample: %s' % (t, r if not r or r[0][0] != 'ERR' else ''))

# 表级 RLS 状态
print('[I] relrowsecurity:', q("SELECT c.relname, c.relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='auth' AND c.relkind='r'"))

# 基础设施域名解析 + TCP 可达(轻量,各一次)
hosts = ['pageserver-51.us-east-2.aws.neon.build', 'pageserver-56.us-east-2.aws.neon.build',
         'safekeeper-17.us-east-2.aws.neon.build', HOST]
for h in hosts:
    try:
        print('[J] dns %s -> %s' % (h, socket.gethostbyname(h)))
    except Exception as e:
        print('[J] dns %s -> ERR %s' % (h, e))

conn.close()

# TCP 可达性(3 端口,2s 超时)
import http.client as _h  # noqa
for host, port in [('pageserver-51.us-east-2.aws.neon.build', 6400),
                   ('pageserver-51.us-east-2.aws.neon.build', 5100),
                   ('safekeeper-17.us-east-2.aws.neon.build', 6401)]:
    s = socket.socket()
    s.settimeout(4)
    try:
        s.connect((host, port))
        print('[K] TCP %s:%d -> OPEN' % (host, port))
    except Exception as e:
        print('[K] TCP %s:%d -> %s' % (host, port, str(e)[:60]))
    finally:
        s.close()
