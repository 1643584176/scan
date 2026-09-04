# -*- coding: utf-8 -*-
"""1) neon_procstat/neon 扩展函数 EXECUTE 测试(owner 能否读任意进程 cmdline)
2) neon_auth schema 表 SELECT 权限探针。完毕清理。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:400]

print('CREATE neon_procstat:', q('CREATE EXTENSION IF NOT EXISTS neon_procstat', fetch=False))
print('CREATE neon:', q('CREATE EXTENSION IF NOT EXISTS neon', fetch=False))
print('CREATE neon_utils:', q('CREATE EXTENSION IF NOT EXISTS neon_utils', fetch=False))

# 1. EXECUTE ACL 检查(函数是否对 PUBLIC/neondb_owner 授权)
print('\n=== [1] EXECUTE ACL ===')
print(q("""
 SELECT p.proname,
   (SELECT array_agg(DISTINCT grantee::text || ':' || privilege_type)
    FROM information_schema.routine_privileges rp
    WHERE rp.routine_name = p.proname AND rp.specific_name = (SELECT specific_name FROM information_schema.routines r WHERE r.routine_name=p.proname LIMIT 1))
 FROM pg_proc p JOIN pg_depend d ON d.objid=p.oid AND d.deptype='e'
 JOIN pg_extension e ON e.oid=d.refobjid AND e.extname IN ('neon_procstat','neon')
 JOIN pg_language l ON l.oid=p.prolang
 WHERE p.proname IN ('neon_proc_pid_all','neon_proc_pid_stat','neon_proc_pid_status','neon_proc_top',
                     'neon_proc_meminfo','neon_proc_loadavg','neon_proc_pid_io','pg_cluster_size','num_cpus')
 ORDER BY p.proname"""))

# 2. 直接 EXECUTE 测试
print('\n=== [2] EXECUTE probes ===')
print('pid1 stat:', q("SELECT pid, comm, left(cmdline, 150) FROM neon_proc_pid_stat(1) LIMIT 1"))
print('pid1 all:', q("SELECT pid, comm, backend_type, left(cmdline, 150) FROM neon_proc_pid_all(1) LIMIT 1"))
print('top:', q("SELECT pid, comm, left(cmdline, 150) FROM neon_proc_top(0) LIMIT 5"))
print('meminfo:', q("SELECT mem_total_kb, mem_free_kb FROM neon_proc_meminfo()"))
print('loadavg:', q("SELECT load1, runnable, last_pid FROM neon_proc_loadavg()"))
print('num_cpus:', q("SELECT num_cpus()"))
print('cluster_size:', q("SELECT pg_cluster_size()"))

# 3. neon_auth 表 SELECT 探针
print('\n=== [3] neon_auth table access ===')
for t in ('user', 'session', 'jwks', 'account', 'organization', 'member', 'project_config', 'invitation', 'verification'):
    r = q('SELECT count(*) FROM neon_auth."%s"' % t)
    print('  neon_auth.%s count: %s' % (t, r))

# 4. 清理
for ext in ('neon_procstat', 'neon_utils', 'neon'):
    print('DROP %s: %s' % (ext, q('DROP EXTENSION IF EXISTS "%s"' % ext, fetch=False)))
print('final ext:', q("SELECT extname FROM pg_extension"))
conn.close()
