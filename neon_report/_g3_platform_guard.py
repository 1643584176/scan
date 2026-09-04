# -*- coding: utf-8 -*-
"""细读:平台防护逻辑源码拉取
1) pg_stat_statements 中 health_check/migration_id/触发器/DO 块完整 SQL(不截断)
2) superuser_check 触发器引用的函数(tgfoid -> prosrc/prosecdef/proacl)
3) postgres 库 public schema 函数清单(health_check_write_succeeds 等)"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_PG = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI_PG, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] 平台初始化/防护 SQL 完整文本 ===')
rows = q("""SELECT calls, query FROM pg_stat_statements
            WHERE query LIKE '%%health_check%%' OR query LIKE '%%migration_id%%' OR query LIKE '%%superuser%%'
               OR query LIKE '%%CREATE TRIGGER%%' OR query LIKE '%%DO $$%%'
            ORDER BY calls DESC""")
if isinstance(rows, list):
    for r in rows:
        print('\n===== calls=%s =====' % r[0])
        print(r[1])
else:
    print('ERR:', rows)

print('\n\n=== [2] 触发器引用函数详情 ===')
print(q("""SELECT c.relname, t.tgname, p.proname, pg_get_userbyid(p.proowner), p.prosecdef,
                  p.proacl::text, p.prosrc
           FROM pg_trigger t
           JOIN pg_class c ON c.oid=t.tgrelid
           JOIN pg_proc p ON p.oid=t.tgfoid
           WHERE NOT t.tgisinternal"""))

print('\n=== [3] postgres 库 public schema 函数 ===')
print(q("""SELECT p.proname, pg_get_function_identity_arguments(p.oid), pg_get_userbyid(p.proowner),
                  p.prosecdef, p.proacl::text
           FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
           WHERE n.nspname='public' ORDER BY 1"""))

print('\n=== [4] neon_migration.migration_id 内容确认 ===')
print(q("SELECT * FROM neon_migration.migration_id"))

print('\n=== [5] lakebase_attributes 是否有保护(触发器/规则对比) ===')
print(q("""SELECT c.relname, t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
           WHERE NOT t.tgisinternal AND c.relname IN ('lakebase_attributes','health_check','migration_id')"""))
print(q("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='lakebase_attributes'"))
print(q("SELECT count(*) FROM public.lakebase_attributes"))

conn.close()
