# -*- coding: utf-8 -*-
"""postgres 库:cron schema 探测 + pg_stat_statements 平台 SQL 轨迹(只读)"""
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

print('=== [1] cron schema 是否存在及对象 ===')
print(q("""SELECT n.nspname, c.relname, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='cron'"""))
print('-- schema acl:', q("SELECT nspacl FROM pg_namespace WHERE nspname='cron'"))

print('=== [2] cron.job 内容(若可读) ===')
print(q("SELECT * FROM cron.job LIMIT 20"))

print('=== [3] pg_stat_statements 可读性 + 平台 SQL 抽样(排除自身) ===')
print(q("""SELECT usename, left(query, 160), calls
  FROM pg_stat_statements WHERE usename='cloud_admin' AND calls > 1
  ORDER BY calls DESC LIMIT 25"""))

print('=== [4] 平台进程最近执行(含 1 次) ===')
print(q("""SELECT usename, left(query, 200), calls
  FROM pg_stat_statements WHERE usename='cloud_admin'
  ORDER BY last_exec_at DESC NULLS LAST LIMIT 20"""))

print('=== [5] cron 相关扩展 ===')
print(q("SELECT extname, extversion FROM pg_extension WHERE extname LIKE '%cron%'"))

conn.close()
