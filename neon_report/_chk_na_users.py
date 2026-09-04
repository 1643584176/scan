# -*- coding: utf-8 -*-
"""只读:neon_auth 表清单 + user 行数(email only, 本地输出)"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=15)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='neon_auth' ORDER BY tablename")
tabs = [r[0] for r in cur.fetchall()]
print('neon_auth tables:', tabs)
for t in tabs:
    try:
        cur.execute('SELECT count(*) FROM neon_auth.%s' % t)
        print('  %s: %s rows' % (t, cur.fetchone()[0]))
    except Exception as e:
        print('  %s: err %s' % (t, e))
# user 表内容(email 列匿名化检查存在性)
for t in ['user', 'users', 'session', 'sessions', 'organization', 'member', 'invitation']:
    if t in tabs:
        try:
            cols = [c[0] for c in cur.execute('SELECT * FROM neon_auth.%s LIMIT 0' % t).description]
            print('  %s cols: %s' % (t, cols))
        except Exception as e:
            print('  %s cols err: %s' % (t, e))
conn.close()
