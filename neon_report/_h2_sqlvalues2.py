# -*- coding: utf-8 -*-
"""修复重拉:auth 函数源码 / neon SQL 函数源码 / pg_stat_statements 全量(含字面值)"""
import psycopg, re

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

print('=== [1] auth 函数源码(pg_session_jwt, 语言 join) ===')
print(q(cur2, """SELECT p.proname, l.lanname, p.prosrc
                 FROM pg_proc p
                 JOIN pg_namespace n ON n.oid=p.pronamespace
                 JOIN pg_language l ON l.oid=p.prolang
                 WHERE n.nspname='auth' ORDER BY p.proname"""))

print('\n=== [2] neon 扩展 SQL/plpgsql 函数源码 ===')
rows = q(cur1, """SELECT p.proname, l.lanname, p.prosrc
                  FROM pg_proc p
                  JOIN pg_namespace n ON n.oid=p.pronamespace
                  JOIN pg_language l ON l.oid=p.prolang
                  WHERE n.nspname='neon' AND l.lanname IN ('sql','plpgsql')
                  ORDER BY 1""")
if isinstance(rows, list):
    for r in rows:
        print('--- %s [%s] ---' % (r[0], r[1]))
        print('   %s' % (r[2] or '')[:1000])
else:
    print('ERR:', rows)

print('\n=== [3] pg_stat_statements 全量(修 userid/dbid 显示) ===')
rows = q(cur1, """SELECT calls,
                         (SELECT rolname FROM pg_roles WHERE oid=userid) AS usr,
                         query
                  FROM pg_stat_statements ORDER BY calls DESC""")
if isinstance(rows, list):
    print('total entries:', len(rows))
    pat = re.compile(r'(https?://|token|secret|password|\.build|\.aws|/var/|/etc/|/tmp|api[_-]?key|eyJ[A-Za-z0-9_-]{10,}|npg_[A-Za-z0-9]+|BEGIN|PRIVATE|KEY)', re.I)
    print('\n--- 含敏感模式字面值 ---')
    for r in rows:
        if isinstance(r[2], str) and pat.search(r[2]):
            print(' calls=%s usr=%s' % (r[0], r[1]))
            print('   %s' % r[2][:700])
    print('\n--- calls>30 高频 ---')
    for r in rows:
        if r[0] and r[0] > 30:
            print(' calls=%s usr=%s' % (r[0], r[1]))
            print('   %s' % (r[2] or '')[:300])
else:
    print('ERR:', rows)

print('\n=== [4] lakebase_attributes 消费链确认 ===')
print('autoscaling flag 值:', q(cur1, "SELECT setting FROM pg_settings WHERE name='neon.autoscaling_state_transfer_enabled'"))
print('sql_exporter 调用证据:')
print(q(cur1, """SELECT calls, query FROM pg_stat_statements
                 WHERE query LIKE '%%primary_memory%%' OR query LIKE '%%get_compute_primary%%'"""))
print('lakebase_attributes 当前行:', q(cur1, "SELECT * FROM public.lakebase_attributes"))
print('函数 ACL:', q(cur1, """SELECT proacl::text FROM pg_proc WHERE proname='get_compute_primary_memory_bytes'
                              AND pronamespace='public'::regnamespace"""))
print('谁拥有写权限(除 owner):', q(cur1, "SELECT relacl::text FROM pg_class WHERE relname='lakebase_attributes'"))

cur1.connection.close()
cur2.connection.close()
