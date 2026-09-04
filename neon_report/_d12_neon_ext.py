# -*- coding: utf-8 -*-
"""重装平台扩展(neon/neon_utils/neon_procstat/postgres_fdw),枚举函数找内部能力
纯枚举+建 server 权限测试,完毕清理。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

for ext in ('neon', 'neon_utils', 'neon_procstat', 'postgres_fdw'):
    print('CREATE %s: %s' % (ext, q('CREATE EXTENSION IF NOT EXISTS "%s"' % ext, fetch=False)))

# 1. 各扩展函数清单
print('\n=== neon functions ===')
print(q("""
 SELECT p.proname, pg_get_function_identity_arguments(p.oid), l.lanname,
        p.provolatile, pg_get_userbyid(p.proowner), p.prosecdef
 FROM pg_proc p JOIN pg_depend d ON d.objid = p.oid AND d.deptype='e'
 JOIN pg_extension e ON e.oid = d.refobjid AND e.extname='neon'
 JOIN pg_language l ON l.oid = p.prolang ORDER BY p.proname"""))
print('\n=== neon_utils functions ===')
print(q("""
 SELECT p.proname, pg_get_function_identity_arguments(p.oid), l.lanname,
        p.provolatile, pg_get_userbyid(p.proowner), p.prosecdef
 FROM pg_proc p JOIN pg_depend d ON d.objid = p.oid AND d.deptype='e'
 JOIN pg_extension e ON e.oid = d.refobjid AND e.extname='neon_utils'
 JOIN pg_language l ON l.oid = p.prolang ORDER BY p.proname"""))
print('\n=== neon_procstat functions ===')
print(q("""
 SELECT p.proname, pg_get_function_identity_arguments(p.oid), l.lanname,
        p.provolatile, pg_get_userbyid(p.proowner), p.prosecdef
 FROM pg_proc p JOIN pg_depend d ON d.objid = p.oid AND d.deptype='e'
 JOIN pg_extension e ON e.oid = d.refobjid AND e.extname='neon_procstat'
 JOIN pg_language l ON l.oid = p.prolang ORDER BY p.proname"""))

# 2. postgres_fdw server 创建权限测试(非 superuser 能否建 server 连任意主机)
print('\n=== fdw server test ===')
q('DROP SERVER IF EXISTS k_fsrv CASCADE', fetch=False)
r = q("CREATE SERVER k_fsrv FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host '127.0.0.1', port '5432', dbname 'postgres')", fetch=False)
print('create server:', r)
if r == 'OK':
    print('server created! (non-superuser fdw server allowed)')
    q('DROP SERVER IF EXISTS k_fsrv CASCADE', fetch=False)
    print('server dropped')

# 3. 清理扩展(保留分析? 不——零破坏,枚举完即清)
for ext in ('neon_procstat', 'neon_utils', 'neon', 'postgres_fdw'):
    print('DROP %s: %s' % (ext, q('DROP EXTENSION IF EXISTS "%s"' % ext, fetch=False)))

conn.close()
