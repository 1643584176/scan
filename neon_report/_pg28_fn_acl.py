# -*- coding: utf-8 -*-
"""函数 EXECUTE ACL 审计(neon/auth/pgrst schema)+ health_check 触发器完整定义 + lakebase 全对象保护状态(只读)"""
import psycopg

URI2 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/postgres'
conn = psycopg.connect(URI2, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

print('=== [1] neon schema 函数 proacl(EXECUTE 权限) ===')
print(q("""SELECT p.proname, p.proacl
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='neon' AND p.proacl IS NOT NULL"""))

print('=== [2] neon schema 函数中 proacl IS NULL 的数量(默认=PUBLIC EXECUTE) ===')
print(q("""SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='neon' AND p.proacl IS NULL"""))

print('=== [3] health_check 上触发器完整定义 ===')
print(q("""SELECT t.tgname, pg_get_triggerdef(t.oid)
  FROM pg_trigger t WHERE t.tgrelid='health_check'::regclass AND NOT t.tgisinternal"""))

print('=== [4] migration_id 触发器 ===')
print(q("""SELECT t.tgname, pg_get_triggerdef(t.oid)
  FROM pg_trigger t WHERE t.tgrelid='neon_migration.migration_id'::regclass AND NOT t.tgisinternal"""))

print('=== [5] lakebase_attributes 全部依赖对象(触发器/规则/约束) ===')
print(q("""SELECT t.tgname, pg_get_triggerdef(t.oid) FROM pg_trigger t
  WHERE t.tgrelid='lakebase_attributes'::regclass AND NOT t.tgisinternal"""))

print('=== [6] lakebase_attributes 的 owner 与 ACLL 之外:table 级默认权限 ===')
print(q("""SELECT pg_get_userbyid(c.relowner), c.relacl, c.relhasrules, c.relhastriggers
  FROM pg_class c WHERE c.relname='lakebase_attributes'"""))

print('=== [7] health_check/lakebase 所在库的 datdba 与库级 ACL ===')
print(q("SELECT datname, pg_get_userbyid(datdba), datacl FROM pg_database WHERE datname IN ('postgres','neondb')"))

print('=== [8] 可写平台表全列清单(确认仅 lakebase_attributes) ===')
print(q("""SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relkind='r' AND n.nspname IN ('public','neon_migration') AND c.relname NOT IN ('health_check','migration_id')
  ORDER BY 1"""))

conn.close()
