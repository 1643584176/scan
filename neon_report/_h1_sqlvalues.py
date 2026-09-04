# -*- coding: utf-8 -*-
"""SQL 值细挖:字面常量 / 函数源码硬编码 / PUBLIC 可执行函数
1) pg_stat_statements 全量 query(不过滤,含低频,找字面值/敏感模式)
2) PUBLIC 可执行函数清单(proacl 含 =X)
3) public/auth schema 函数 prosrc 全文(pg_session_jwt + 平台函数)
4) pgrst.pre_config() 实际调用(租户可 PUBLIC EXECUTE)
5) neon 扩展 SQL/plpgsql 函数 prosrc(可读的)"""
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

print('=== [1] pg_stat_statements 全量(含低频/含字面值) ===')
rows = q(cur1, """SELECT calls, userid::regrole::text, dbid::regdatabase::text, query
                  FROM pg_stat_statements ORDER BY calls DESC""")
if isinstance(rows, list):
    print('total entries:', len(rows))
    # 先找含可疑字面值的(URL/token/路径/长串)
    pat = re.compile(r'(https?://|token|secret|password|\.build|\.aws|/var/|/etc/|/tmp|api[_-]?key|eyJ[A-Za-z0-9_-]{10,})', re.I)
    print('\n--- 含敏感模式字面值的 query ---')
    for r in rows:
        if pat.search(r[3] or ''):
            print(' calls=%s user=%s db=%s' % (r[0], r[1], r[2]))
            print('   %s' % (r[3] or '')[:900])
    print('\n--- calls>50 的高频 query 全部 ---')
    for r in rows:
        if r[0] and r[0] > 50:
            print(' calls=%s user=%s' % (r[0], r[1]))
            print('   %s' % (r[3] or '')[:400])
else:
    print('ERR:', rows)

print('\n=== [2] PUBLIC 可执行函数(=X 或含 PUBLIC) ===')
print(q(cur2, """SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid),
                        pg_get_userbyid(p.proowner), p.proacl::text
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE p.proacl::text LIKE '%%=X/%%' OR p.proacl::text LIKE '%%PUBLIC%%'
                 ORDER BY 1,2"""))
print(q(cur1, """SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid),
                        pg_get_userbyid(p.proowner), p.proacl::text
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE p.proacl::text LIKE '%%=X/%%' OR p.proacl::text LIKE '%%PUBLIC%%'
                 ORDER BY 1,2"""))

print('\n=== [3] public 函数源码全文 ===')
for f in ('health_check_write_succeeds', 'get_compute_primary_memory_bytes'):
    print('--- %s ---' % f)
    print(q(cur1, "SELECT prosrc FROM pg_proc WHERE proname='%s' AND pronamespace='public'::regnamespace" % f))

print('\n=== [4] auth 函数源码(pg_session_jwt) ===')
print(q(cur2, """SELECT p.proname, p.language::reglanguage::text, p.prosrc
                 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE n.nspname='auth' ORDER BY p.proname"""))

print('\n=== [5] pgrst.pre_config() 实际调用 ===')
print(q(cur2, "SELECT pgrst.pre_config()"))

print('\n=== [6] neon 扩展可读源码函数(SQL/plpgsql) ===')
rows = q(cur1, """SELECT p.proname, p.language::reglanguage::text, p.prosrc
                  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                  WHERE n.nspname='neon' AND p.language::reglanguage::text IN ('sql','plpgsql')
                  ORDER BY 1""")
for r in rows or []:
    print('--- %s [%s] ---' % (r[0], r[1]))
    print('   %s' % (r[2] or '')[:800])

cur1.connection.close()
cur2.connection.close()
