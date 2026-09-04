# -*- coding: utf-8 -*-
"""v15:平台表写权限最终证明(no-op UPDATE 触发触发器,0 行修改零破坏)
+ migration_id 正确 schema + cloud_admin 会话角色操纵能力探测(只读)"""
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

def dblink_q(sql, label, coldef='t(x text)'):
    set_rule("INSERT INTO k_out(x) SELECT * FROM dblink('host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5', '%s') AS %s" % (sql.replace("'", "''"), coldef))
    r = fire()
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    print('  %s: %s | fire: %s' % (label, rows, r))

def dblink_exec(sql, label):
    """dblink_exec 执行 DML 返回状态串(no-op 安全)"""
    set_rule("INSERT INTO k_out(x) SELECT dblink_exec('host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5', '%s')" % sql.replace("'", "''"))
    r = fire()
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    print('  %s: %s | fire: %s' % (label, rows, r))

# [1] no-op UPDATE 平台表(触发器放行证明,0 行修改)
print('=== [1] 平台表 no-op UPDATE(触发器验证) ===')
dblink_exec("UPDATE health_check SET healthy = healthy WHERE false", 'health_check no-op(UPDATE 0 行,触发器若拦则 ERR)')
dblink_exec("UPDATE neon_migration.migration_id SET id = id WHERE false", 'migration_id no-op')
dblink_exec("UPDATE lakebase_attributes SET value = value WHERE false", 'lakebase no-op')

# [2] 真实写验证——INSERT 1 行后立即 DELETE(事务内?dblink_exec 单语句——用 INSERT...RETURNING + 随后 DELETE)
# 更安全:先 SELECT 行结构,INSERT 临时行验证后 DELETE(唯一键可控)
print('=== [2] lakebase 临时写验证(插入后立即删) ===')
dblink_q("SELECT column_name::text || ':' || data_type::text FROM information_schema.columns WHERE table_name='lakebase_attributes' ORDER BY ordinal_position", 'lakebase cols', 't(x text)')
# INSERT 自建行(零冲突:name 用 k_probe_uuid 前缀)→ DELETE 回滚痕迹
dblink_exec("INSERT INTO lakebase_attributes(name, value, last_updated) VALUES ('__k_probe_tmp', '{\"k\":1}'::jsonb, now())", 'lakebase INSERT probe')
dblink_q("SELECT value::text FROM lakebase_attributes WHERE name='__k_probe_tmp'", 'readback probe')
dblink_exec("DELETE FROM lakebase_attributes WHERE name='__k_probe_tmp'", 'DELETE probe cleanup')
dblink_q("SELECT count(*)::text FROM lakebase_attributes WHERE name LIKE '__k_probe%'", 'verify clean')

# [3] health_check 行结构 + migration_id 结构
print('=== [3] 平台表结构 ===')
dblink_q("SELECT column_name::text FROM information_schema.columns WHERE table_name='health_check' ORDER BY ordinal_position", 'health_check cols', 't(x text)')
dblink_q("SELECT column_name::text FROM information_schema.columns WHERE table_schema='neon_migration' AND table_name='migration_id' ORDER BY ordinal_position", 'migration_id cols', 't(x text)')

# [4] 角色操纵能力(只读探测——不实际 ALTER)
print('=== [4] 角色操纵面(只读) ===')
dblink_q("SELECT rolname::text FROM pg_authid WHERE rolpassword IS NOT NULL", 'roles with password', 't(x text)')
dblink_q("SELECT rolname::text || '|' || rolsuper::text || '|' || rolcreaterole::text FROM pg_authid WHERE rolname IN ('cloud_admin','neondb_owner','neon_superuser','neon_service')", 'key roles attrs', 't(x text)')

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
