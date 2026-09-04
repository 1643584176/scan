# -*- coding: utf-8 -*-
"""postgres 库 owner 直连深测:读内容/写权限(ROLLBACK 验证)/建表/schema 全景
零破坏:写测试全部 BEGIN+ROLLBACK,建表即删。"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:400]

# 1. schema 全景
print('=== [1] schemas ===')
print(q("SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema' ORDER BY 1"))
print('non-pub tables:', q("SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('public') ORDER BY 1,2"))

# 2. 平台表读内容
print('\n=== [2] platform tables read ===')
print('health_check row:', q('SELECT * FROM health_check'))
print('lakebase_attributes cols:', q("""SELECT a.attname, format_type(a.atttypid,a.atttypmod) FROM pg_attribute a
  JOIN pg_class c ON c.oid=a.attrelid WHERE c.relname='lakebase_attributes' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))
print('lakebase_attributes count:', q('SELECT count(*) FROM lakebase_attributes'))

# 3. 写权限(事务 ROLLBACK 零残留)
print('\n=== [3] write perms (tx rollback) ===')
conn.autocommit = False
try:
    cur.execute('BEGIN')
    cur.execute('UPDATE health_check SET healthy = healthy WHERE false')
    print('UPDATE no-op: OK')
    cur.execute('ROLLBACK')
except Exception as e:
    print('UPDATE no-op ERR:', str(e)[:300])
    try: cur.execute('ROLLBACK')
    except Exception: pass
try:
    cur.execute('BEGIN')
    cur.execute("INSERT INTO lakebase_attributes (id) VALUES (0) ON CONFLICT DO NOTHING")
    print('INSERT probe: OK(有插入能力或 ON CONFLICT 吞错)')
    cur.execute('ROLLBACK')
except Exception as e:
    print('INSERT probe ERR:', str(e)[:300])
    try: cur.execute('ROLLBACK')
    except Exception: pass
conn.autocommit = True

# 4. 建表/建函数权限(即建即删)
print('\n=== [4] DDL perms ===')
print('create table:', q('CREATE TABLE k_tmp(id int)', fetch=False))
print('drop table:', q('DROP TABLE IF EXISTS k_tmp', fetch=False))
print('create fn:', q("CREATE FUNCTION k_f() RETURNS int AS 'SELECT 1' LANGUAGE sql", fetch=False))
print('drop fn:', q('DROP FUNCTION IF EXISTS k_f()', fetch=False))

# 5. 库级 ACL/表 ACL 细节
print('\n=== [5] ACL detail ===')
print(q("SELECT c.relname, c.relacl FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'"))
print('datacl:', q("SELECT datname, datacl FROM pg_database WHERE datname='postgres'"))

conn.close()
