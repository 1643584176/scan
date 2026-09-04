# -*- coding: utf-8 -*-
"""role_names 注入残留角色取证(纯只读)
目标:确定 x"; CREATE ROLE pwn LOGIN; -- 与 pwn 的创建身份/权限(平台 vs 租户)
零破坏:仅 SELECT"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, args=None, fetch=True):
    try:
        cur.execute(sql, args or ())
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

print('=== [1] 残留角色全属性 ===')
print(q("""SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin,
                  rolreplication, rolbypassrls, rolconnlimit, rolvaliduntil, oid
           FROM pg_roles
           WHERE rolname IN ('pwn', 'x"; CREATE ROLE pwn LOGIN; --')
           ORDER BY oid"""))

print('\n=== [2] 全部角色按 oid 倒序(找最近创建/残留) ===')
print(q("""SELECT rolname, rolsuper, rolcreaterole, rolcanlogin, oid
           FROM pg_roles WHERE rolname !~ '^pg_'
           ORDER BY oid DESC LIMIT 15"""))

print('\n=== [3] 可疑角色的组成员关系(若为平台组角色成员=>平台创建) ===')
for rn in ('pwn', 'x"; CREATE ROLE pwn LOGIN; --'):
    print(q("""SELECT m.rolname AS member, g.rolname AS grp, a.admin_option
               FROM pg_auth_members a
               JOIN pg_roles m ON m.oid = a.member
               JOIN pg_roles g ON g.oid = a.roleid
               WHERE m.rolname = %s""", (rn,)))

print('\n=== [4] neondb_owner 可 ADMIN 的角色集 ===')
print(q("""SELECT g.rolname, a.admin_option
           FROM pg_auth_members a JOIN pg_roles g ON g.oid=a.roleid
           WHERE a.member = (SELECT oid FROM pg_roles WHERE rolname='neondb_owner')"""))
print('neondb_owner 是哪些组的成员:')
print(q("""SELECT g.rolname, a.admin_option
           FROM pg_auth_members a JOIN pg_roles g ON g.oid=a.roleid
           JOIN pg_roles m ON m.oid=a.member
           WHERE m.rolname='neondb_owner'"""))

print('\n=== [5] 尝试 SET ROLE / 连接属性(只读探测) ===')
for rn in ('pwn', 'x"; CREATE ROLE pwn LOGIN; --'):
    r = q('SET ROLE %s' % psycopg.sql.Identifier(rn), fetch=False)
    print('SET ROLE %s: %s' % (rn, r))
    if r == 'OK':
        print('   current_user:', q('SELECT current_user, session_user'))
        q('RESET ROLE', fetch=False)

print('\n=== [6] pwn 相关清理残留扫描 ===')
print(q("""SELECT rolname FROM pg_roles WHERE rolname ILIKE '%pwn%' OR rolname ILIKE '%sec3%' OR rolname ILIKE '%k_%'"""))

print('\n=== [7] 最近角色 oid 对照(判断创建时间线) ===')
print(q("""SELECT rolname, oid FROM pg_roles
           WHERE rolname IN ('neondb_owner','neon_auth','authenticator','cloud_admin','neon_superuser','anonymous','authenticated','pwn')
           ORDER BY oid"""))

conn.close()
