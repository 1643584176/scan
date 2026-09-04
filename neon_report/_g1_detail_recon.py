# -*- coding: utf-8 -*-
"""细读侦察(纯只读):把前几轮粗看的地方变细看
1) pg_stat_activity 平台连接完整 query/客户端地址/时长
2) pg_stat_statements 平台 SQL 全文
3) postgres 平台库全表+行数+内容细读(health_check/migration_id)
4) pg_db_role_setting(平台对角色/库的 GUC 设置--之前没查过)
5) postgres 库规则/触发器现状 + 全库 definer 函数
6) schema 分布(修正旧查询 bug)+ pg_language"""
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

def q(cur, sql, args=None):
    try:
        cur.execute(sql, args or ())
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

print('=== [1] pg_stat_activity 平台连接全字段 ===')
rows = q(cur2, """SELECT pid, datname, usename, application_name, client_addr, client_port,
                         backend_start, xact_start, state_change, state, wait_event_type, wait_event,
                         query
                  FROM pg_stat_activity WHERE backend_type='client backend' ORDER BY usename, pid""")
for r in rows or []:
    print('---')
    print(' pid=%s db=%s user=%s app=%s client=%s state=%s wait=%s/%s start=%s xact=%s' % (
        r[0], r[1], r[2], r[3], r[4], r[8], r[10], r[11], r[6], r[7]))
    print(' query:', (r[12] or '')[:1500])

print('\n=== [2] pg_stat_statements 平台 SQL 全文(top 40 by calls, 过滤自己) ===')
rows = q(cur1, """SELECT calls, rows, left(query, 2000) AS q
                  FROM pg_stat_statements
                  WHERE query NOT LIKE '%%k_%%' AND query NOT LIKE '%%pg_stat_statements%%'
                    AND userid IN (SELECT oid FROM pg_roles WHERE rolname IN ('cloud_admin','neon_auth','authenticator'))
                  ORDER BY calls DESC LIMIT 40""")
if isinstance(rows, list):
    for r in rows:
        print(' calls=%s rows=%s' % (r[0], r[1]))
        print('   %s' % (r[2] or '')[:800])
else:
    print('ERR:', rows)

print('\n=== [3] postgres 平台库全部表 + 行数 ===')
rows = q(cur1, """SELECT n.nspname, c.relname, c.relkind,
                         pg_get_userbyid(c.relowner), c.relacl::text
                  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                  WHERE n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
                    AND c.relkind IN ('r','p','v','m','f')
                  ORDER BY 1,2""")
if isinstance(rows, list):
    for r in rows:
        print('  %s.%s kind=%s owner=%s acl=%s' % (r[0], r[1], r[2], r[3], (r[4] or '')[:120]))
else:
    print('ERR:', rows)

print('\n=== [4] 平台表内容细读 ===')
for t in ('health_check', 'migration_id'):
    cols = q(cur1, "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='%s'" % t)
    print('  %s cols: %s' % (t, [c[0] for c in (cols or [])]))
    if isinstance(cols, list):
        cnt = q(cur1, 'SELECT count(*) FROM public.%s' % t)
        print('  %s rows: %s' % (t, cnt))
        if isinstance(cnt, list) and cnt and cnt[0][0] and int(cnt[0][0]) <= 50:
            data = q(cur1, 'SELECT * FROM public.%s' % t)
            for d in (data or []):
                print('    ', str(d)[:500])

print('\n=== [5] pg_db_role_setting(角色/库级 GUC 设置) ===')
rows = q(cur2, """SELECT d.datname, r.rolname, s.setconfig
                  FROM pg_db_role_setting s
                  LEFT JOIN pg_database d ON d.oid = s.setdatabase
                  LEFT JOIN pg_roles r ON r.oid = s.setrole
                  ORDER BY 1 NULLS FIRST, 2 NULLS FIRST""")
for r in rows or []:
    print('  db=%-12s role=%-20s config=%s' % (r[0], r[1], r[2]))

print('\n=== [6] postgres 库规则/触发器现状 ===')
print('rules(排除视图内部):')
print(q(cur1, """SELECT c.relname, r.rulename, pg_get_ruledef(r.oid)
                 FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
                 WHERE r.rulename NOT LIKE '_RETURN'"""))
print('triggers:')
print(q(cur1, """SELECT c.relname, t.tgname, pg_get_userbyid(t.tgowner), t.tgenabled
                 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                 WHERE NOT t.tgisinternal"""))

print('\n=== [7] 全库 SECURITY DEFINER 函数(非 pg_catalog) ===')
print(q(cur1, """SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner), p.proacl::text
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog','information_schema')
                 ORDER BY 1,2"""))

print('\n=== [8] schema 分布(修正版,两库) ===')
for label, cur in (('postgres', cur1), ('neondb', cur2)):
    rows = q(cur, """SELECT n.nspname, count(c.oid)
                     FROM pg_namespace n LEFT JOIN pg_class c ON c.relnamespace=n.oid
                     WHERE n.nspname NOT IN ('pg_toast','pg_temp_1','pg_toast_temp_1')
                     GROUP BY 1 ORDER BY 2 DESC""")
    print('--', label)
    for r in (rows or []):
        print('   %-40s %s' % (r[0], r[1]))

print('\n=== [9] pg_language / 关键 GUC 当前值 ===')
print(q(cur2, "SELECT lanname, lanpltrusted, pg_get_userbyid(lanowner) FROM pg_language"))
print(q(cur2, """SELECT name, setting FROM pg_settings WHERE name IN
                 ('session_replication_role','row_security','default_transaction_read_only','statement_timeout','idle_in_transaction_session_timeout','lock_timeout')"""))

print('\n=== [10] neondb public schema 函数(非扩展) ===')
print(q(cur2, """SELECT p.proname, pg_get_userbyid(p.proowner), p.prosecdef
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE n.nspname='public' ORDER BY 1"""))

cur1.connection.close()
cur2.connection.close()
