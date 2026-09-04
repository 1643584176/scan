# -*- coding: utf-8 -*-
import psycopg
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
for t in ['user', 'session', 'account', 'invitation', 'organization', 'member', 'verification', 'project_config']:
    try:
        cur.execute('SELECT count(*) FROM neon_auth.%s' % t)
        print('%s: %s rows' % (t, cur.fetchone()[0]))
    except Exception as e:
        print(t, 'err:', e)
# invitation 全量(找我们的邀请行)
cur.execute("""SELECT id, "organizationId", email, role, status FROM neon_auth.invitation ORDER BY "createdAt" DESC LIMIT 10""")
for r in cur.fetchall():
    print('inv:', str(r)[:250])
# user 行数按 email
cur.execute("""SELECT email, "emailVerified" FROM neon_auth.user WHERE email LIKE 'libobo1229%%' ORDER BY email""")
for r in cur.fetchall():
    print('user:', r)
conn.close()
