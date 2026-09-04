# -*- coding: utf-8 -*-
"""权限模型复核:neondb_owner 角色属性/pg_authid ACL/成员链 + 直读 vs RULE 列级对比 + pwn 残留检查(全只读)"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] neondb_owner 角色属性 ===')
print(q("""SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin,
  rolreplication, rolbypassrls FROM pg_roles WHERE rolname='neondb_owner'"""))

print('=== [2] pg_authid 表 ACL ===')
print(q("SELECT relacl FROM pg_class WHERE oid='pg_authid'::regclass"))

print('=== [3] neondb_owner 的直接成员(可 SET ROLE 的目标) ===')
print(q("""SELECT r.rolname FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid
  WHERE m.member=(SELECT oid FROM pg_roles WHERE rolname='neondb_owner')"""))

print('=== [4] 直读 pg_authid 的 rolpassword 列级(长度聚合,不打印内容) ===')
print(q("""SELECT count(*), count(rolpassword) FROM pg_authid"""))

print('=== [5] pwn 注入残留检查 ===')
print(q("SELECT rolname, rolsuper FROM pg_roles WHERE rolname LIKE '%pwn%' OR rolname LIKE 'x%'"))

print('=== [6] cloud_admin/neon_service 成员与 superuser ===')
print(q("""SELECT rolname, rolsuper FROM pg_roles
  WHERE rolname IN ('cloud_admin','neon_service','neon_superuser','authenticator','neon_auth')"""))

conn.close()
