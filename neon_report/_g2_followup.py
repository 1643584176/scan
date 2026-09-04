# -*- coding: utf-8 -*-
"""细读跟进:
1) neon_migration.migration_id 内容(平台迁移状态)
2) postgres 库触发器(修正列名)+ neon 视图定义
3) auth schema 函数(pg_session_jwt)详情 + ACL
4) health_check 心跳频率/执行者确认(pg_stat_statements 两次采样)
5) 平台表行级 ACL 细节(health_check/lakebase_attributes 的列权限?)"""
import psycopg, time

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
        return 'ERR: %s' % str(e)[:250]

print('=== [1] neon_migration 内容 ===')
print(q(cur1, "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='neon_migration'"))
print(q(cur1, "SELECT * FROM neon_migration.migration_id"))
print('schema 对象:', q(cur1, "SELECT c.relname, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='neon_migration'"))

print('\n=== [2] postgres 库触发器(修正) ===')
print(q(cur1, """SELECT c.relname, t.tgname, pg_get_userbyid(c.relowner), t.tgenabled, t.tgtype
                 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                 WHERE NOT t.tgisinternal"""))
print('health_check 的列级权限:')
print(q(cur1, """SELECT attname, attacl::text FROM pg_attribute
                 WHERE attrelid='public.health_check'::regclass AND attacl IS NOT NULL"""))

print('\n=== [3] auth/neon_auth schema 函数详情 ===')
print('auth schema 函数:')
print(q(cur2, """SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid), pg_get_userbyid(p.proowner),
                        p.prosecdef, p.proacl::text
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE n.nspname IN ('auth','pgrst','neon_auth','extensions') ORDER BY 1,2"""))
print('pg_session_jwt 扩展对象分布:')
print(q(cur2, """SELECT e.extname, n.nspname, count(*)
                 FROM pg_depend d
                 JOIN pg_extension e ON e.oid=d.refobjid
                 JOIN pg_class c ON c.oid=d.objid
                 JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE e.extname='pg_session_jwt' AND d.classid='pg_class'::regclass
                 GROUP BY 1,2"""))
print('pg_session_jwt 扩展属主:', q(cur2, "SELECT pg_get_userbyid(extowner) FROM pg_extension WHERE extname='pg_session_jwt'"))

print('\n=== [4] health_check 心跳频率确认(两次采样 12 秒) ===')
def hb_stats():
    return q(cur1, """SELECT calls, rows, left(query,150) FROM pg_stat_statements
                      WHERE query LIKE '%%health_check%%' OR query LIKE '%%migration_id%%'""")
s1 = hb_stats()
print('t0:', s1)
time.sleep(12)
s2 = hb_stats()
print('t12:', s2)

print('\n=== [5] neon 视图定义细读(找底层函数/表线索) ===')
for v in ('neon_lfc_stats', 'neon_backend_perf_counters', 'neon_stat_file_cache', 'neon_backpressure_status'):
    d = q(cur1, "SELECT pg_get_viewdef('%s.neon.%s'::regclass, true)" % ('', v))
    print('-- %s:' % v)
    print('  ', str(d)[:600])

print('\n=== [6] pg_stat_activity 快照连续采样 3 次(抓短连接) ===')
for i in range(3):
    rows = q(cur2, """SELECT datname, usename, application_name, client_addr, state, query
                      FROM pg_stat_activity WHERE backend_type='client backend'""")
    for r in rows or []:
        if r[1] != 'neondb_owner':
            print('  [%d] %s/%s app=%s from=%s state=%s q=%s' % (i, r[0], r[1], r[2], r[3], r[4], (r[5] or '')[:80]))
    time.sleep(2)

cur1.connection.close()
cur2.connection.close()
