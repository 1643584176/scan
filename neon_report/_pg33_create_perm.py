# -*- coding: utf-8 -*-
"""收尾:postgres 库各 schema CREATE 权限(事务回滚)+ 全库 RLS 策略清单确认(只读)"""
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
        return 'ERR: %s' % str(e)[:200]

print('=== [1] postgres 库各 schema 的 CREATE 权限(事务回滚) ===')
for sch in ('public', 'neon', 'neon_migration'):
    try:
        cur.execute('BEGIN')
        cur.execute('CREATE TABLE %s.k_probe (id int)' % sch)
        print(' ', sch, '-> CREATE OK(回滚)')
        cur.execute('ROLLBACK')
    except Exception as e:
        cur.execute('ROLLBACK')
        print(' ', sch, '-> DENIED:', str(e)[:120])

print('=== [2] postgres 库全部 RLS 策略 ===')
print(q("""SELECT n.nspname, c.relname, p.polname, p.polpermissive, p.polroles::regrole[]
  FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace"""))

print('=== [3] 引用 auth.* 函数的对象(全库,找消费方) ===')
print(q("""SELECT DISTINCT n.nspname, c.relname, pg_get_expr(c.relacl, c.oid) IS NOT NULL AS has_acl
  FROM pg_depend d JOIN pg_proc p ON p.oid=d.refobjid
  JOIN pg_class c ON c.oid=d.objid JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE p.proname IN ('uid','user_id','session','organization','organization_id','jwt')
  AND d.refclassid='pg_proc'::regclass AND d.classid='pg_class'::regclass"""))

print('=== [4] 视图/函数定义中引用 auth.(全库) ===')
print(q("""SELECT n.nspname, p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE pg_get_functiondef(p.oid) LIKE '%auth.%' AND n.nspname NOT IN ('pg_catalog','information_schema')
  AND n.nspname <> 'auth'"""))
conn.close()
