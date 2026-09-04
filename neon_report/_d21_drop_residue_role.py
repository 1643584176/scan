# -*- coding: utf-8 -*-
"""清理 d10 审计发现的残留角色(早前角色名注入测试遗留,rolcanlogin=True)
仅删除该精确角色名;不存在则跳过。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
NAME = 'x"; CREATE ROLE pwn LOGIN; --'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

cur.execute('SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = %s', (NAME,))
row = cur.fetchone()
print('role exists:', row)
if row:
    # 确认无依赖(角色未被任何对象 owner/被授予)
    cur.execute("""SELECT count(*) FROM pg_class WHERE relowner = (SELECT oid FROM pg_roles WHERE rolname=%s)""", (NAME,))
    owns = cur.fetchone()[0]
    cur.execute("""SELECT count(*) FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname=%s)
                    OR member=(SELECT oid FROM pg_roles WHERE rolname=%s)""", (NAME, NAME))
    mem = cur.fetchone()[0]
    print('owns objects:', owns, '| memberships:', mem)
    if owns == 0 and mem == 0:
        cur.execute('DROP ROLE "%s"' % NAME.replace('"', '""'))
        print('dropped')
    else:
        print('SKIP: has dependencies')
conn.close()
