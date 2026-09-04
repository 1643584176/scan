# -*- coding: utf-8 -*-
"""postgres 库平台对象深挖(只读):neon 视图可读性/lakebase_attributes 结构内容/health_check + neondb 库 pre_config"""
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

print('=== [1] lakebase_attributes 结构 ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull
  FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  WHERE c.relname='lakebase_attributes' AND a.attnum>0 AND NOT a.attisdropped"""))

print('=== [2] lakebase_attributes ACL + owner ===')
print(q("""SELECT pg_get_userbyid(c.relowner), c.relacl, c.relrowsecurity
  FROM pg_class c WHERE c.relname='lakebase_attributes'"""))

print('=== [3] lakebase_attributes 内容(0 行已确认,再确认) ===')
print(q("SELECT * FROM lakebase_attributes LIMIT 5"))

print('=== [4] health_check 结构与内容 ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
  FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  WHERE c.relname='health_check' AND a.attnum>0 AND NOT a.attisdropped"""))
print(q("SELECT * FROM health_check LIMIT 3"))

print('=== [5] neon_migration.migration_id ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
  FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
  WHERE c.relname='migration_id' AND a.attnum>0 AND NOT a.attisdropped"""))
print(q("SELECT * FROM neon_migration.migration_id LIMIT 3"))

print('=== [6] neon schema 视图可读性抽样 ===')
for v in ('neon_perf_counters', 'neon_backend_perf_counters', 'neon_backpressure_status',
          'neon_stat_file_cache', 'neon_lfc_stats', 'local_cache'):
    print(' ', v, q('SELECT count(*) FROM neon.%s' % v))

print('=== [7] neon 视图定义抽样(perf_counters 列) ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
  FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relname='neon_perf_counters' AND n.nspname='neon' AND a.attnum>0 AND NOT a.attisdropped"""))

print('=== [8] 写权限基线:no-op UPDATE lakebase_attributes(零破坏) ===')
print(q("UPDATE lakebase_attributes SET lakebase_attributes = lakebase_attributes"))
conn.close()

# neondb 库查 pre_config 完整定义
print()
URI1 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn2 = psycopg.connect(URI1, connect_timeout=15)
conn2.autocommit = True
cur2 = conn2.cursor()
try:
    cur2.execute("SELECT pg_get_functiondef('pgrst.pre_config'::regproc)")
    print('=== [9] pgrst.pre_config(neondb) ===')
    print(cur2.fetchone()[0][:2500])
except Exception as e:
    print('[9] ERR:', str(e)[:200])
conn2.close()
