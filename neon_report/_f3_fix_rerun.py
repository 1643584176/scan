# -*- coding: utf-8 -*-
"""修复重跑:GUC 扫描(%%转义) / 成员链 / 平台连接 datname 视角 / ALTER DATABASE 影响面
纯只读"""
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

print('=== [1] 自定义 GUC(postgres 库,%%转义) ===')
print(q(cur1, """SELECT name, setting, vartype, source FROM pg_settings
                 WHERE name LIKE '%%neon%%' OR name LIKE '%%.%%' OR name LIKE '%%auth%%' OR name LIKE '%%token%%' OR name LIKE '%%secret%%'
                 ORDER BY name LIMIT 50"""))

print('\n=== [2] 自定义 GUC(neondb 库) ===')
print(q(cur2, """SELECT name, setting, vartype, source FROM pg_settings
                 WHERE name LIKE '%%neon%%' OR name LIKE '%%.%%' OR name LIKE '%%auth%%' OR name LIKE '%%token%%' OR name LIKE '%%secret%%'
                 ORDER BY name LIMIT 50"""))

print('\n=== [3] neondb_owner 的 pg_ 预定义角色成员 ===')
print(q(cur2, """SELECT g.rolname FROM pg_auth_members a
                 JOIN pg_roles g ON g.oid=a.roleid
                 JOIN pg_roles m ON m.oid=a.member
                 WHERE m.rolname='neondb_owner'"""))
print('递归含 pg_signal_backend/pg_checkpoint/pg_create_subscription?')
print(q(cur2, """SELECT rolname FROM pg_roles
                 WHERE pg_has_role('neondb_owner', oid, 'member') AND rolname LIKE 'pg_%%'"""))

print('\n=== [4] 平台连接连哪个库(datname 视角) ===')
print(q(cur2, """SELECT datname, usename, application_name, state, left(query,50) AS q
                 FROM pg_stat_activity WHERE backend_type='client backend'"""))

print('\n=== [5] 其他库有无平台连接(postgres 库视角) ===')
print(q(cur1, """SELECT datname, usename, application_name, state
                 FROM pg_stat_activity WHERE backend_type='client backend'"""))

print('\n=== [6] 订阅/发布/复制槽(逻辑复制面) ===')
print('publications:', q(cur2, "SELECT * FROM pg_publication"))
print('subscriptions:', q(cur2, "SELECT * FROM pg_subscription"))
print('repl slots:', q(cur2, "SELECT slot_name, slot_type, active FROM pg_replication_slots"))
print('can create subscription?', q(cur2, "SELECT pg_has_role('neondb_owner','pg_create_subscription','member')"))
print('wal_level:', q(cur2, "SELECT setting FROM pg_settings WHERE name='wal_level'"))

print('\n=== [7] pg_read_all_settings 视角:superuser-only GUC 可见性 ===')
print(q(cur1, """SELECT name, setting FROM pg_settings WHERE name IN
                 ('data_directory','config_file','hba_file','unix_socket_directories','listen_addresses','port',
                  'shared_preload_libraries','local_preload_libraries','session_preload_libraries','dynamic_library_path')"""))
print(q(cur1, "SELECT name, setting FROM pg_settings WHERE source='external' OR source='override' LIMIT 20"))

print('\n=== [8] pg_stat_database/冲突/归档(平台侧计数器) ===')
print(q(cur1, """SELECT datname, numbackends, xact_commit, xact_rollback, blks_read, blks_hit
                 FROM pg_stat_database WHERE datname IN ('neondb','postgres')"""))

print('\n=== [9] ALTER DATABASE neondb 潜在影响对象确认 ===')
print(q(cur2, """SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='neondb'"""))
print('neondb 库上的活动平台连接数:')
print(q(cur2, """SELECT count(*) FROM pg_stat_activity WHERE datname='neondb'
                 AND usename NOT IN ('neondb_owner') AND backend_type='client backend'"""))

cur1.connection.close()
cur2.connection.close()
