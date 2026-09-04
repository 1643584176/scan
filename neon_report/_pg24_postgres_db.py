# -*- coding: utf-8 -*-
"""postgres 平台库探测(只读)+ pgrst.pre_config 完整定义"""
import psycopg

# 连接 postgres 库试试
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

print('=== [1] 连接成功,当前库与角色 ===')
print(q("SELECT current_database(), current_user"))

print('=== [2] postgres 库对象清单 ===')
print(q("""SELECT n.nspname, c.relname, c.relkind, pg_get_userbyid(c.relowner), c.relrowsecurity
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg\\_toast%'
  ORDER BY 1,2,3"""))

print('=== [3] postgres 库表行数(可读的表) ===')
for n, t in q("""SELECT schemaname, tablename FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1,2"""):
    if isinstance(n, str):
        r = q('SELECT count(*) FROM %s.%s' % (n, t))
        print(' ', n, t, r)
    else:
        break

print('=== [4] postgres 库 SECURITY DEFINER ===')
print(q("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner)
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog','information_schema')"""))

print('=== [5] pgrst.pre_config 完整定义 ===')
cur2 = conn.cursor()
cur2.execute("SELECT pg_get_functiondef('pgrst.pre_config'::regproc)")
print(cur2.fetchone()[0][:2000])
conn.close()
