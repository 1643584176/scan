# -*- coding: utf-8 -*-
"""neondb 主库:租户可装扩展白名单探测(逐扩展独立事务 ROLLBACK 零残留)
目标:pg_repack 之外被放行的扩展;若可装则列出对象与函数,找可利用面"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

print('已安装扩展基线:', end=' ')
cur.execute("SELECT extname FROM pg_extension ORDER BY 1")
print([r[0] for r in cur.fetchall()])

CANDS = ['pg_cron', 'vector', 'lakebase_text', 'lakebase_vector', 'lakebase_tokenizer',
         'rag', 'neon_monitor', 'neon_utils', 'neon_procstat', 'pg_partman',
         'pgaudit', 'hypopg', 'pg_hint_plan', 'timescaledb', 'pgjwt', 'pg_graphql',
         'pg_repack', 'dblink', 'pg_surgery', 'pg_walinspect', 'lo', 'file_fdw',
         'pg_prewarm', 'pg_buffercache', 'amcheck', 'pg_visibility', 'hll', 'ip4r',
         'roaringbitmap', 'pg_search', 'pg_tiktoken', 'semver', 'pg_uuidv7']

for ext in CANDS:
    try:
        cur.execute('BEGIN')
    except Exception:
        pass
    try:
        cur.execute('CREATE EXTENSION IF NOT EXISTS "%s"' % ext)
        cur.execute("""SELECT extname, extversion, pg_get_userbyid(extowner)
                       FROM pg_extension WHERE extname=%s""", (ext,))
        info = cur.fetchall()
        # 新 schema/对象
        cur.execute("""SELECT n.nspname, c.relname, c.relkind, pg_get_userbyid(c.relowner)
                       FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                       WHERE n.nspname IN ('public') AND c.relname LIKE '%%%s%%'""" % ext.lower()[:10].replace('_',''))
        rels = cur.fetchall()
        # 函数
        cur.execute("""SELECT p.proname, pg_get_userbyid(p.proowner), p.prosecdef, p.provolatile
                       FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                       WHERE n.nspname='public'
                       ORDER BY p.proname LIMIT 0""")
        print('[INSTALL-OK] %s | %s | public rels=%s' % (ext, info, rels))
    except Exception as e:
        msg = str(e)[:120].replace('\n', ' ')
        print('[DENIED] %s: %s' % (ext, msg))
    try:
        cur.execute('ROLLBACK')
    except Exception:
        pass

cur.execute("""SELECT extname FROM pg_extension""")
print('\n终验残留:', cur.fetchall())
conn.close()
