# -*- coding: utf-8 -*-
"""Data API 面侦察[2]:角色成员关系全景(authenticator 能 SET ROLE 到谁?)
+ public schema 表/ACL + 特殊角色属性。全只读。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

print('=== [1] 全部角色成员关系(member_of <- member) ===')
print(q("""SELECT g.rolname AS member_of, m.rolname AS member
          FROM pg_auth_members am
          JOIN pg_roles g ON g.oid = am.roleid
          JOIN pg_roles m ON m.oid = am.member
          ORDER BY 1, 2"""))

print('\n=== [2] 特殊角色属性 ===')
print(q("""SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin,
          rolbypassrls, rolconfig
          FROM pg_roles
          WHERE rolname IN ('authenticator','authenticated','anonymous','neondb_owner',
                            'cloud_admin','neon_superuser','neon_service','anon','neon_auth')"""))

print('\n=== [3] public schema 对象 + 表级 ACL ===')
print(q("""SELECT c.relname, c.relkind, pg_get_userbyid(c.relowner),
          array_to_string(c.relacl, ' | ') AS acl
          FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = 'public' AND c.relkind IN ('r','p','v','S')
          ORDER BY c.relkind, c.relname"""))

print('\n=== [4] 默认权限(public schema 未来对象) ===')
print(q("""SELECT pg_get_userbyid(d.defaclrole) AS owner, defaclobjtype,
          array_to_string(d.defaclacl, ' | ') AS acl
          FROM pg_default_acl d JOIN pg_namespace n ON n.oid = d.defaclnamespace
          WHERE n.nspname = 'public'"""))

print('\n=== [5] neondb_owner 自己建的表(Data API 可见对象) ===')
print(q("""SELECT c.relname, c.relkind,
          array_to_string(c.relacl, ' | ') AS acl
          FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = 'public' AND pg_get_userbyid(c.relowner) = 'neondb_owner'"""))

conn.close()
