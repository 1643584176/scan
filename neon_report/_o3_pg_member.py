# -*- coding: utf-8 -*-
import psycopg
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""SELECT table_name FROM information_schema.tables
               WHERE table_schema='neon_auth' ORDER BY table_name""")
print('tables:', [r[0] for r in cur.fetchall()])
for t in ['organization', 'member']:
    try:
        cur.execute('SELECT * FROM neon_auth.%s LIMIT 5' % t)
        cols = [d[0] for d in cur.description]
        print('\n%s cols: %s' % (t, cols))
        for r in cur.fetchall():
            print(' ', str(r)[:300])
    except Exception as e:
        print(t, 'err:', e)
conn.close()
