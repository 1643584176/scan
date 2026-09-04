# -*- coding: utf-8 -*-
"""细节验证:pg_maintain SET FALSE 断链 + web_access + default privileges + 触发器行级确认"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_PG = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
URI_ND = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)

def mk(uri):
    c = psycopg.connect(uri, connect_timeout=20)
    c.autocommit = True
    return c.cursor()

cur1 = mk(URI_PG)
cur2 = mk(URI_ND)

def q(cur, sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] pg_auth_members inherit 标志(neon_superuser 的成员关系) ===')
print(q(cur2, """SELECT g.rolname AS parent, m.rolname AS member,
                        a.admin_option, a.inherit_option
                 FROM pg_auth_members a
                 JOIN pg_roles g ON g.oid=a.roleid
                 JOIN pg_roles m ON m.oid=a.member
                 WHERE g.rolname IN ('pg_read_all_data','pg_write_all_data','pg_maintain','pg_monitor','pg_signal_backend','pg_create_subscription','pg_signal_autovacuum_worker','neon_superuser')
                 ORDER BY 1,2"""))

print('\n=== [2] neondb_owner 的实际可继承权限(不是成员,是继承) ===')
print(q(cur2, """SELECT g.rolname FROM pg_auth_members a
                 JOIN pg_roles g ON g.oid=a.roleid
                 JOIN pg_roles m ON m.oid=a.member
                 WHERE m.rolname='neondb_owner' AND a.inherit_option"""))
print('间接(经 neon_superuser 链,inherit 检查):')
print(q(cur2, """WITH RECURSIVE chain AS (
                   SELECT roleid, member, inherit_option FROM pg_auth_members WHERE member='neondb_owner'::regrole
                   UNION ALL
                   SELECT am.roleid, am.member, am.inherit_option
                   FROM pg_auth_members am JOIN chain c ON am.member = c.roleid
                   WHERE c.inherit_option
                 )
                 SELECT g.rolname FROM chain JOIN pg_roles g ON g.oid=chain.roleid WHERE chain.inherit_option"""))

print('\n=== [3] 实际验证:VACUUM/REINDEX health_check(maintain 权限) ===')
print(q(cur1, "VACUUM public.health_check"))
print(q(cur1, "REINDEX TABLE public.health_check"))

print('\n=== [4] web_access / 其他特殊角色 ===')
print(q(cur2, """SELECT rolname FROM pg_roles
                 WHERE rolname NOT LIKE 'pg_%' AND rolname NOT IN
                 ('neondb_owner','neon_superuser','cloud_admin','neon_auth','authenticator','authenticated','anonymous','neon_service','k_evt_role_781149')
                 ORDER BY 1"""))

print('\n=== [5] ALTER DEFAULT PRIVILEGES 现状(public schema) ===')
print(q(cur1, """SELECT pg_get_userbyid(defaclrole), defaclobjtype, defaclacl::text
                 FROM pg_default_acl d JOIN pg_namespace n ON n.oid=d.defaclnamespace
                 WHERE n.nspname='public'"""))

print('\n=== [6] 触发器行级/语句级确认 ===')
print(q(cur1, """SELECT c.relname, t.tgname, t.tgtype, t.tgconstraint, t.tgnargs
                 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                 WHERE NOT t.tgisinternal"""))
print('tgtype 解码: 1=ROW 2=BEFORE 4=INSERT 8=DELETE 16=UPDATE 32=TRUNCATE 64=AFTER 128=CONSTRAINT')

print('\n=== [7] 写保护实测(事务回滚,应 DENIED) ===')
print(q(cur1, "BEGIN; INSERT INTO public.health_check VALUES (1, now()); ROLLBACK"))
print(q(cur1, "BEGIN; UPDATE neon_migration.migration_id SET id=99; ROLLBACK"))
print(q(cur1, "BEGIN; DELETE FROM public.health_check; ROLLBACK"))

cur1.connection.close()
cur2.connection.close()
