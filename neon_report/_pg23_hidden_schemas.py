# -*- coding: utf-8 -*-
"""隐藏 schema(auth/pgrst)对象审计 + pg_session_jwt 函数定义(全只读)"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] auth/pgrst schema 全部对象(pg_class 全 relkind) ===')
print(q("""SELECT n.nspname, c.relname, c.relkind, pg_get_userbyid(c.relowner)
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname IN ('auth','pgrst') ORDER BY 1,2"""))

print('=== [2] auth/pgrst 函数 ===')
print(q("""SELECT n.nspname, p.proname, p.prosecdef, pg_get_userbyid(p.proowner),
  left(pg_get_functiondef(p.oid), 300)
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname IN ('auth','pgrst') ORDER BY 1,2"""))

print('=== [3] auth/pgrst 类型 ===')
print(q("""SELECT n.nspname, t.typname FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
  WHERE n.nspname IN ('auth','pgrst') AND t.typtype IN ('c','e','r') ORDER BY 1,2"""))

print('=== [4] pg_session_jwt 函数(全 schema) ===')
print(q("""SELECT n.nspname, p.proname, p.prosecdef, pg_get_userbyid(p.proowner), p.proargnames, p.prosrc
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE p.proname IN ('set_session_jwt','clear_session_jwt','pgrst_','is_session_jwt_valid','session_jwt_claims')
  OR p.proname LIKE '%session%jwt%' ORDER BY 1,2"""))

print('=== [5] auth schema 权限 ===')
print(q("SELECT nspname, pg_get_userbyid(nspowner), nspacl FROM pg_namespace WHERE nspname IN ('auth','pgrst')"))

print('=== [6] 是否有其他库可连 ===')
print(q("SELECT datname, pg_get_userbyid(datdba) FROM pg_database WHERE datallowconn"))

conn.close()
