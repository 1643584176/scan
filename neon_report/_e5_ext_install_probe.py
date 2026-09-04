# -*- coding: utf-8 -*-
"""租户可装扩展白名单探测(逐扩展独立事务 ROLLBACK 零残留)
目标:找出 pg_repack 之外被 Neon 放行的扩展,及其中是否有可利用对象"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

CANDS = ['pg_cron', 'vector', 'lakebase_text', 'lakebase_vector', 'lakebase_tokenizer',
         'rag', 'neon_monitor', 'neon_utils', 'neon_procstat', 'pg_partman',
         'pgaudit', 'hypopg', 'pg_hint_plan', 'timescaledb', 'pgjwt', 'pg_graphql',
         'pg_repack', 'dblink', 'pg_surgery', 'pg_walinspect', 'lo']

for ext in CANDS:
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    try:
        cur.execute('CREATE EXTENSION IF NOT EXISTS "%s"' % ext)
        cur.execute("""SELECT extname, extversion, pg_get_userbyid(extowner) FROM pg_extension WHERE extname=%s""", (ext,))
        info = cur.fetchall()
        cur.execute("""SELECT n.nspname, count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                       WHERE n.nspname NOT IN ('pg_catalog','information_schema')
                       GROUP BY 1 ORDER BY 1""")
        objs = cur.fetchall()
        cur.execute("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner), p.prosecdef, p.provolatile
                       FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                       WHERE n.nspname IN ('public') AND p.proname LIKE '%' || %s || '%'
                       ORDER BY 1,2 LIMIT 10""", ('',))
        funcs = cur.fetchall()
        print('[INSTALL-OK] %s | %s | objs=%s | public funcs=%s' % (ext, info, objs, funcs[:3]))
    except Exception as e:
        msg = str(e)[:150].replace('\n', ' ')
        print('[DENIED/ERR] %s: %s' % (ext, msg))
    try:
        cur.execute('ROLLBACK')
    except Exception:
        pass

# 终验:无残留
cur.execute("""SELECT extname FROM pg_extension WHERE extname IN
               ('pg_cron','vector','lakebase_text','lakebase_vector','lakebase_tokenizer','rag',
                'neon_monitor','neon_utils','neon_procstat','pg_partman','pgaudit','hypopg',
                'pg_hint_plan','timescaledb','pgjwt','pg_graphql','pg_repack','dblink',
                'pg_surgery','pg_walinspect','lo')""")
print('\n残留扩展:', cur.fetchall())
conn.close()
