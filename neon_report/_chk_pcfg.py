# -*- coding: utf-8 -*-
"""只读:project_config 表结构与内容(本地输出)"""
import psycopg, json

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=15)
cur = conn.cursor()
cols = [c[0] for c in cur.execute('SELECT * FROM neon_auth.project_config LIMIT 0').description]
print('project_config cols:', cols)
cur.execute('SELECT * FROM neon_auth.project_config')
rows = cur.fetchall()
for r in rows:
    print('row:')
    for c, v in zip(cols, r):
        s = str(v)
        print('  %s: %s' % (c, s[:600]))
conn.close()
