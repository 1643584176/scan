# -*- coding: utf-8 -*-
"""扩展白名单测试:owner 能 CREATE 哪些扩展(逐个试,记录成败与错误)
成功后立即 DROP 清理(零破坏)。file_fdw/postgres_fdw/pg_cron 为重点。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

cands = ['file_fdw', 'postgres_fdw', 'pg_cron', 'neon_utils', 'neon', 'neon_monitor',
         'neon_procstat', 'pageinspect', 'pg_surgery', 'pg_stat_statements', 'hll',
         'anon', 'pgaudit', 'pg_jsonschema', 'sslinfo', 'xml2']
for ext in cands:
    r = q('CREATE EXTENSION IF NOT EXISTS "%s"' % ext, fetch=False)
    if r == 'OK':
        # 成功:记录函数数,然后 DROP
        n = q("SELECT count(*) FROM pg_proc p JOIN pg_extension e ON e.oid = p.extnamespace WHERE e.extname='%s'" % ext)
        d = q('DROP EXTENSION IF EXISTS "%s"' % ext, fetch=False)
        print('[%s] INSTALL-OK (fns=%s) then %s' % (ext, n, d))
    else:
        print('[%s] %s' % (ext, r))

conn.close()
