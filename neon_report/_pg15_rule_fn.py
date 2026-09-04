# -*- coding: utf-8 -*-
"""复查 RULE+函数:C 场景细测(函数返回 current_user 而非建表,观察执行身份)"""
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

q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("CREATE TABLE k_src(id int, v text)", fetch=False)
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
print('oid:', oid)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)

# 场景 C 细测:函数返回 current_user + 副作用计数表
q("DROP TABLE IF EXISTS k_cnt", fetch=False)
q("CREATE TABLE k_cnt(n int)", fetch=False)
q("DROP FUNCTION IF EXISTS k_rulefn2()", fetch=False)
q("""CREATE FUNCTION k_rulefn2() RETURNS text LANGUAGE plpgsql AS $q$
BEGIN
  EXECUTE 'INSERT INTO k_cnt VALUES (1)';
  RETURN current_user;
END $q$""", fetch=False)
q("DROP TABLE IF EXISTS k_via_rfn2", fetch=False)
q("CREATE TABLE k_via_rfn2(u text)", fetch=False)
q("DROP RULE IF EXISTS r3 ON repack.log_%d" % oid, fetch=False)
q("CREATE RULE r3 AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_via_rfn2 SELECT k_rulefn2()" % oid, fetch=False)
print('[C2] insert:', q("INSERT INTO k_src VALUES (6,'x')", fetch=False))
print('[C2] k_cnt:', q("SELECT * FROM k_cnt"))
print('[C2] k_via_rfn2:', q("SELECT * FROM k_via_rfn2"))

# 场景 E:直接调用用户函数(非 rule,模拟 definer 上下文直接 SELECT)不可行——无 definer 函数;改用:log 表 column DEFAULT 函数
q("DROP TABLE IF EXISTS repack.log2_%d" % oid, fetch=False)
q("CREATE TABLE repack.log2_%d (pk repack.pk_%d, row k_src, extra text DEFAULT k_rulefn2())" % (oid, oid), fetch=False)
q("DROP RULE IF EXISTS r3 ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t3 ON k_src", fetch=False)
# 直接把 repack_trigger 指向 log2? 不行,名字固定 log_<oid>。改为替换 log_oid 为带 DEFAULT 版本
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src, extra text DEFAULT k_rulefn2())" % (oid, oid), fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)
print('[E default-fn] insert:', q("INSERT INTO k_src VALUES (7,'x')", fetch=False))
print('[E] k_cnt after default:', q("SELECT * FROM k_cnt"))

# 清理
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP RULE IF EXISTS r3 ON repack.log_%d" % oid, fetch=False)
q("DROP FUNCTION IF EXISTS k_rulefn2()", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_cnt", fetch=False)
q("DROP TABLE IF EXISTS k_via_rfn2", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS repack.log2_%d" % oid, fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('cleanup:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
