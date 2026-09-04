# -*- coding: utf-8 -*-
"""neondb 库 RLS 策略 + auth.* 消费方确认(只读)"""
import psycopg

URI1 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI1, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] neondb 库全部 RLS 策略 ===')
print(q("""SELECT n.nspname, c.relname, p.polname, p.polroles::text
  FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace"""))

print('=== [2] neondb 库 RLS 开启的表 ===')
print(q("""SELECT n.nspname, c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relrowsecurity AND c.relkind='r'"""))

print('=== [3] 依赖 auth schema 函数的对象 ===')
print(q("""SELECT DISTINCT n.nspname, c.relname FROM pg_depend d
  JOIN pg_proc p ON p.oid=d.refobjid AND d.refclassid='pg_proc'::regclass
  JOIN pg_rewrite rw ON rw.oid=d.objid AND d.classid='pg_rewrite'::regclass
  JOIN pg_class c ON c.oid=rw.ev_class JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE p.pronamespace='auth'::regnamespace"""))

print('=== [4] 函数体引用 auth. 的函数(排除 auth schema 自身) ===')
print(q("""SELECT n.nspname, p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname NOT IN ('auth','pg_catalog','information_schema')
  AND p.prosrc LIKE '%auth.%' OR p.prosqlbody::text LIKE '%auth.%'"""))

conn.close()
