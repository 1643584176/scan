# -*- coding: utf-8 -*-
"""数据库面独立新洞侦察:纯 neondb_owner 会话(零提权依赖)
审计 owner 直接能力 + 扩展清单 + SECURITY DEFINER 函数清单 + 平台对象暴露
全部只读/可逆,无 repack 载体,无残留。"""
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

# 1. 身份基线
print('[1] current_user:', q('SELECT current_user, session_user'))
print('    is_superuser:', q('SHOW is_superuser'))
print('    roles:', q("SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication FROM pg_roles ORDER BY 1"))

# 2. 危险内置函数直测(owner 直接调,预期 pre-escalation denied)
print('[2] pg_read_file:', q("SELECT pg_read_file('/etc/hostname')"))
print('    pg_ls_dir:', q("SELECT pg_ls_dir('/etc')"))
print('    pg_read_binary_file:', q("SELECT length(pg_read_binary_file('/etc/hostname'))"))
print('    lo_import:', q("SELECT lo_import('/etc/hostname')"))

# 3. 扩展清单(已装 vs 可用)
print('[3] installed:', q("SELECT extname, extversion FROM pg_extension ORDER BY 1"))
print('    available-all:', q("SELECT name, default_version FROM pg_available_extensions ORDER BY 1"))
print('    avail-net:', q("SELECT name FROM pg_available_extensions WHERE name IN ('dblink','pg_net','http','plpython3u','plperl','postgres_fdw','file_fdw','pg_curl','pgsql-http','wrappers','pg_cron','uuid-ossp','pg_stat_statements')"))

# 4. SECURITY DEFINER 函数审计(找 repack_trigger 之外的 definer 对象)
print('[4] secdef C fns:', q("""
    SELECT p.proname, n.nspname, l.lanname, pg_get_userbyid(p.proowner), p.provolatile
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_language l ON l.oid = p.prolang
    WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY n.nspname, p.proname LIMIT 40"""))
print('    secdef all count:', q("""
    SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema')"""))

# 5. 平台对象暴露:非标准 schema/表
print('[5] schemas:', q("SELECT nspname FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema','public') AND nspname NOT LIKE 'pg_%' ORDER BY 1"))
print('    non-pub tables:', q("""
    SELECT schemaname, tablename FROM pg_tables
    WHERE schemaname NOT IN ('public','pg_catalog','information_schema') ORDER BY 1,2 LIMIT 30"""))
print('    all tables count:', q("SELECT count(*) FROM pg_tables WHERE schemaname='public'"))

conn.close()
