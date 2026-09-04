# -*- coding: utf-8 -*-
"""全库对象图景审计(只读):schema/表/RLS/ACL/SECURITY DEFINER/触发器/扩展——找未注意的面"""
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

print('=== [1] 全部 schema(非系统) ===')
print(q("""SELECT nspname, pg_get_userbyid(nspowner) FROM pg_namespace
  WHERE nspname NOT LIKE 'pg\\_%' AND nspname <> 'information_schema' ORDER BY 1"""))

print('=== [2] 每 schema 的表/视图/物化视图 ===')
print(q("""SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT LIKE 'pg\\_%' AND schemaname<>'information_schema'
  ORDER BY 1,2"""))
print('-- views:')
print(q("""SELECT schemaname, viewname FROM pg_views WHERE schemaname NOT LIKE 'pg\\_%' AND schemaname<>'information_schema'
  ORDER BY 1,2"""))
print('-- matviews:')
print(q("""SELECT schemaname, matviewname FROM pg_matviews WHERE schemaname NOT LIKE 'pg\\_%' AND schemaname<>'information_schema'"""))

print('=== [3] 所有表的 RLS 状态 + owner + ACL ===')
print(q("""SELECT n.nspname, c.relname, pg_get_userbyid(c.relowner), c.relrowsecurity, c.relforcerowsecurity, c.relacl
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relkind='r' AND n.nspname NOT LIKE 'pg\\_%' AND n.nspname<>'information_schema'
  ORDER BY 1,2"""))

print('=== [4] 全部 SECURITY DEFINER 函数(含系统 schema 外的所有) ===')
print(q("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner)
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog','information_schema')
  ORDER BY 1,2"""))

print('=== [5] 触发器函数 + 事件触发器 ===')
print(q("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner), p.prosrc IS NOT NULL
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE p.proname LIKE '%.trigger%' OR p.prokind='f' AND p.prosrc LIKE '%trigger%'
  AND n.nspname NOT IN ('pg_catalog','information_schema')"""))
print('-- event triggers:')
print(q("SELECT evtname, evtevent, pg_get_userbyid(evtowner) FROM pg_event_trigger"))

print('=== [6] 序列/大对象/外部表 ===')
print(q("""SELECT n.nspname, c.relname, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relkind IN ('S','f','L','p') AND n.nspname NOT LIKE 'pg\\_%' AND n.nspname<>'information_schema'"""))

print('=== [7] 已安装扩展 ===')
print(q("SELECT extname, extversion, pg_get_userbyid(extowner) FROM pg_extension"))

print('=== [8] 用户可写但非 owner 的表(潜在直写面) ===')
print(q("""SELECT n.nspname, c.relname, pg_get_userbyid(c.relowner), c.relacl
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relkind='r' AND n.nspname NOT LIKE 'pg\\_%' AND n.nspname<>'information_schema'
  AND pg_get_userbyid(c.relowner) <> 'neondb_owner' ORDER BY 1,2"""))

conn.close()
