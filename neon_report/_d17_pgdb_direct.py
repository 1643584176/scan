# -*- coding: utf-8 -*-
"""postgres 库直连测试:owner 能否经外部 proxy 连 dbname=postgres(平台表所在库)
+ pg_database 库清单。若通=平台表直读候选(独立于 cloud_admin 链)。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'

# 1. 库清单(owner 视角)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT datname, pg_get_userbyid(datdba), datallowconn FROM pg_database ORDER BY 1")
print('databases:', cur.fetchall())
cur.execute("SELECT current_database()")
print('current db:', cur.fetchall())
conn.close()

# 2. 外部直连 dbname=postgres
for db in ('postgres', 'neondb'):
    try:
        c2 = psycopg.connect('postgresql://neondb_owner:%s@%s/%s' % (PWD, HOST, db), connect_timeout=15)
        c2.autocommit = True
        cu = c2.cursor()
        cu.execute('SELECT current_user, current_database(), (SELECT rolsuper FROM pg_roles WHERE rolname=current_user)')
        print('connect %s OK: %s' % (db, cu.fetchall()))
        # 看表权限
        cu.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")
        tbls = cu.fetchall()
        print('  public tables (%d): %s' % (len(tbls), tbls[:15]))
        for t in ('health_check',):
            try:
                cu.execute('SELECT count(*) FROM public.%s' % t)
                print('  SELECT %s count: %s' % (t, cu.fetchall()))
            except Exception as e:
                print('  SELECT %s ERR: %s' % (t, str(e)[:200]))
        c2.close()
    except Exception as e:
        print('connect %s FAIL: %s' % (db, str(e)[:200]))
