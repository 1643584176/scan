# -*- coding: utf-8 -*-
"""平台防写机制分析:health_check/migration_id 的规则与触发器 + neon_check_for_superuser 定义 + 全平台表保护覆盖"""
import psycopg

URI2 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/postgres'
conn = psycopg.connect(URI2, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        if fetch:
            return cur.fetchall()
        return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

print('=== [1] postgres 库所有表上的 RULE ===')
print(q("""SELECT c.relname, r.rulename, r.ev_type, r.is_instead
  FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
  WHERE r.rulename <> '_RETURN' AND c.relkind='r'"""))

print('=== [2] 所有触发器 ===')
print(q("""SELECT c.relname, t.tgname, pg_get_userbyid(t.tgowner)
  FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
  WHERE NOT t.tgisinternal"""))

print('=== [3] neon_check_for_superuser 定义 ===')
print(q("""SELECT p.proname, p.prosecdef, pg_get_userbyid(p.proowner),
  pg_get_functiondef(p.oid) FROM pg_proc p
  WHERE p.proname LIKE '%check%superuser%' OR p.proname LIKE '%superuser%'"""))

print('=== [4] neon schema 全部函数 ===')
print(q("""SELECT p.proname, pg_get_userbyid(p.proowner), p.prosecdef, left(pg_get_functiondef(p.oid), 200)
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='neon'"""))

print('=== [5] 保护覆盖对比:各平台表 UPDATE/INSERT(事务回滚) ===')
for t in ('health_check', 'neon_migration.migration_id', 'lakebase_attributes'):
    try:
        cur.execute('BEGIN')
        cur.execute('UPDATE %s SET %s = %s WHERE 1=0' % (t, 'id' if 'migration' in t else 'value', 'id' if 'migration' in t else 'value'))
        cur.execute('ROLLBACK')
        print(' ', t, '-> UPDATE writable')
    except Exception as e:
        cur.execute('ROLLBACK')
        print(' ', t, '-> DENIED:', str(e)[:120])

print('=== [6] lakebase_attributes 相关:有无同 schema 其他可写对象 ===')
print(q("""SELECT n.nspname, c.relname, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname IN ('public','neon','neon_migration') AND c.relkind IN ('r','S')
  ORDER BY 1,2"""))

conn.close()
