# -*- coding: utf-8 -*-
"""neon_auth schema 表 ACL 审计 + authenticated 角色直连可读性"""
import psycopg, json

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

# 1) neon_auth schema 全部表 + ACL
cur.execute("""
SELECT c.relname, pg_get_userbyid(c.relowner),
       COALESCE(ARRAY_TO_STRING(ARRAY(
           SELECT grantee::regrole::text || ':' || privilege_type
           FROM aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner)))
       ), ', '), '(default: owner only)')
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'neon_auth' AND c.relkind IN ('r', 'p')
ORDER BY c.relname
""")
print('== neon_auth tables ACL ==', flush=True)
for r in cur.fetchall():
    print('%-22s owner=%-14s ACL=%s' % (r[0], r[1], r[2]), flush=True)

# 2) neon_auth schema USAGE 权限
cur.execute("""
SELECT nspname, pg_get_userbyid(nspowner),
       COALESCE(ARRAY_TO_STRING(ARRAY(
           SELECT grantee::regrole::text || ':' || privilege_type
           FROM aclexplode(COALESCE(nspacl, acldefault('n', nspowner)))
       ), ', '), '(default)')
FROM pg_namespace WHERE nspname = 'neon_auth'
""")
for r in cur.fetchall():
    print('schema ACL:', r, flush=True)

# 3) 各角色成员关系
cur.execute("""
SELECT r.rolname, m.rolname AS member_of
FROM pg_roles r LEFT JOIN pg_auth_members am ON am.member = r.oid
LEFT JOIN pg_roles m ON m.oid = am.roleid
WHERE r.rolname IN ('neondb_owner','neon_auth','authenticated','anonymous','authenticator','cloud_admin','neon_superuser')
ORDER BY r.rolname
""")
print('\n== role memberships ==', flush=True)
for r in cur.fetchall():
    print(r, flush=True)
conn.close()
print('done', flush=True)
