# -*- coding: utf-8 -*-
"""清理: DROP 测试残留的 postgres_fdw/dblink 扩展"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)

c = psycopg.connect(URI, connect_timeout=20)
c.autocommit = True
cur = c.cursor()

def q(sql):
    try:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return 'OK(no rows)'
    except Exception as e:
        return 'ERR: %s' % str(e)[:150]

print('清理前:', q("SELECT extname FROM pg_extension WHERE extname IN ('postgres_fdw','dblink')"))
print(q("DROP EXTENSION IF EXISTS postgres_fdw CASCADE"))
print(q("DROP EXTENSION IF EXISTS dblink CASCADE"))
print('清理后 ext:', q("SELECT extname FROM pg_extension WHERE extname IN ('postgres_fdw','dblink')"))
print('server:', q("SELECT srvname FROM pg_foreign_server"))
print('mapping:', q("SELECT count(*) FROM pg_user_mapping"))
print('ft:', q("SELECT relname FROM pg_class WHERE relname LIKE 'k_fdw%' OR relname LIKE 'k_c_%'"))
print('ts:', q("SELECT spcname FROM pg_tablespace WHERE spcname LIKE 'k_%'"))
print('schema:', q("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'k_%'"))
print('role:', q("SELECT rolname FROM pg_roles WHERE rolname LIKE 'k_%'"))
c.close()
print('清理完成')
