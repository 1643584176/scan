# -*- coding: utf-8 -*-
"""pg_stat_statements 平台 SQL 轨迹 v2(userid join)"""
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

print('=== [1] pg_stat_statements 列结构 ===')
print(q("""SELECT a.attname FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  WHERE c.relname='pg_stat_statements' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))

print('=== [2] 平台 SQL 轨迹(cloud_admin, 高频) ===')
print(q("""SELECT left(query, 200), calls, mean_exec_time::int
  FROM pg_stat_statements WHERE userid=(SELECT oid FROM pg_roles WHERE rolname='cloud_admin')
  AND calls > 1 ORDER BY calls DESC LIMIT 30"""))

print('=== [3] 全部角色 SQL 概况 ===')
print(q("""SELECT r.rolname, count(*) FROM pg_stat_statements s
  JOIN pg_roles r ON r.oid=s.userid GROUP BY 1"""))

print('=== [4] 低频/特殊 SQL(含 lakebase 关键字) ===')
print(q("""SELECT left(query, 250), calls FROM pg_stat_statements
  WHERE lower(query) LIKE '%lakebase%' OR lower(query) LIKE '%health_check%' OR lower(query) LIKE '%migration%'
  LIMIT 20"""))
conn.close()
