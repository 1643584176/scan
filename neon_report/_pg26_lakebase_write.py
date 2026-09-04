# -*- coding: utf-8 -*-
"""lakebase 写权限基线(正确列名 no-op)+ neon 视图内容抽样 + health 表写基线(全零破坏)"""
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

print('=== [1] lakebase no-op UPDATE(0 行条件,值不变) ===')
print(q("UPDATE lakebase_attributes SET value = value WHERE name = '__k_noexist__'"))

print('=== [2] lakebase INSERT 权限(事务内回滚=零破坏) ===')
try:
    cur.execute("BEGIN")
    cur.execute("INSERT INTO lakebase_attributes(name, value, last_updated) VALUES ('__k_test__', '{}', now())")
    print('  insert OK(将回滚)')
    cur.execute("ROLLBACK")
    print('  rolled back')
except Exception as e:
    cur.execute("ROLLBACK")
    print('  insert DENIED:', str(e)[:200])

print('=== [3] health_check no-op UPDATE ===')
print(q("UPDATE health_check SET updated_at = updated_at WHERE id = 999999"))

print('=== [4] neon_migration no-op UPDATE ===')
print(q("UPDATE neon_migration.migration_id SET id = id WHERE key = 999999"))

print('=== [5] neon_backend_perf_counters 内容抽样 ===')
print(q("SELECT metric, bucket_le, value FROM neon.neon_backend_perf_counters LIMIT 8"))

print('=== [6] neon_perf_counters 内容抽样 ===')
print(q("SELECT metric, bucket_le, value FROM neon.neon_perf_counters LIMIT 8"))

print('=== [7] local_cache 内容抽样 ===')
print(q("SELECT * FROM neon.local_cache LIMIT 5"))

print('=== [8] neon_backpressure_status 内容抽样 ===')
print(q("SELECT * FROM neon.neon_backpressure_status LIMIT 5"))
conn.close()
