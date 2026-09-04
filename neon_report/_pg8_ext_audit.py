# -*- coding: utf-8 -*-
"""PG 深度审计 A:扩展面 + 全量 SECURITY DEFINER(含系统 schema) + 事件触发器 + 平台对象"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, n=80):
    try:
        cur.execute(sql)
        return cur.fetchall()[:n]
    except Exception as e:
        return [('ERR', str(e)[:150])]

print('=== [1] 高价值可用扩展 ===')
for r in q("""SELECT name, default_version FROM pg_available_extensions
   WHERE name IN ('pg_repack','amcheck','pg_cron','pg_hint_plan','hypopg','pg_prewarm','auto_explain',
   'pg_stat_statements','pg_surgery','pageinspect','pg_readonly','anon','postgres_fdw','dblink','lo','uuid-ossp',
   'pgcrypto','pgsodium','supabase_vault','neon','pg_net','pgjwt','pg_graphql','pgaudit','credcheck')
   ORDER BY 1""", 60):
    print('  ', r)

print('\n=== [2] 已安装扩展 + owner ===')
for r in q("""SELECT e.extname, e.extversion, pg_get_userbyid(e.extowner), n.nspname
   FROM pg_extension e JOIN pg_namespace n ON n.oid = e.extnamespace ORDER BY 1"""):
    print('  ', r)

print('\n=== [3] 全量 SECURITY DEFINER(所有 schema,含扩展) ===')
for r in q("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner), p.prosecdef
   FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE p.prosecdef AND n.nspname NOT IN ('information_schema')
   ORDER BY 1,2""", 150):
    print('  ', r)

print('\n=== [4] 事件触发器 ===')
for r in q("""SELECT evtname, pg_get_userbyid(evtowner), evtevent, evtenabled FROM pg_event_trigger"""):
    print('  ', r)

print('\n=== [5] 所有 schema + owner ===')
for r in q("""SELECT nspname, pg_get_userbyid(nspowner) FROM pg_namespace
   WHERE nspname NOT LIKE 'pg\_%' AND nspname <> 'information_schema' ORDER BY 1"""):
    print('  ', r)

print('\n=== [6] 平台/系统 schema 中的表(非 public/neon_auth) ===')
for r in q("""SELECT schemaname, tablename FROM pg_tables
   WHERE schemaname NOT IN ('public','neon_auth','pg_catalog','information_schema') ORDER BY 1,2"""):
    print('  ', r)

conn.close()
