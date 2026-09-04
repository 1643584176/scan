# -*- coding: utf-8 -*-
"""cloud_admin/neon_superuser/neon_service 角色属性 + 当前用户成员链"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin,
   rolreplication, rolbypassrls, rolconnlimit
   FROM pg_roles WHERE rolname IN ('neondb_owner','cloud_admin','neon_superuser','neon_service',
   'anonymous','authenticated','authenticator','pg_database_owner') ORDER BY 1""")
print('=== 角色属性 ===')
for r in cur.fetchall():
    print('  ', r)

print('\n=== neondb_owner 的角色成员链 ===')
cur.execute("""WITH RECURSIVE chain AS (
    SELECT m.roleid::regrole AS r, m.member::regrole AS m, 1 AS d
    FROM pg_auth_members m WHERE m.member::regrole::text = 'neondb_owner'
    UNION ALL
    SELECT m.roleid::regrole, m.member::regrole, c.d+1 FROM pg_auth_members m JOIN chain c ON m.member = c.r)
SELECT DISTINCT r::text FROM chain ORDER BY 1""")
for r in cur.fetchall():
    print('  member of:', r[0])

print('\n=== cloud_admin 能访问的系统对象(superuser 检查) ===')
cur.execute('SELECT current_setting(%s)', ('is_superuser',))
print('neondb_owner is_superuser:', cur.fetchone())
cur.execute("""SELECT has_table_privilege('cloud_admin','pg_authid','SELECT')""")
print('cloud_admin read pg_authid:', cur.fetchone()[0])
cur.execute("""SELECT has_table_privilege('cloud_admin','pg_user_mappings','SELECT')""")
print('cloud_admin read pg_user_mappings:', cur.fetchone()[0])
cur.execute("""SELECT has_function_privilege('cloud_admin','pg_read_file(text)','EXECUTE')""")
print('cloud_admin exec pg_read_file:', cur.fetchone()[0])
cur.execute("""SELECT has_function_privilege('cloud_admin','pg_ls_dir(text)','EXECUTE')""")
print('cloud_admin exec pg_ls_dir:', cur.fetchone()[0])
conn.close()
