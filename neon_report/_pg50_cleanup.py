# -*- coding: utf-8 -*-
"""中断后残留清理确认"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

# 1. 先看残留
print('[before] public tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('[before] repack objects:', q("SELECT tablename FROM pg_tables WHERE schemaname='repack'"))
print('[before] types:', q("SELECT typname FROM pg_type WHERE typname LIKE 'pk\\_%' ESCAPE '\\'"))
print('[before] triggers:', q("SELECT tgname FROM pg_trigger WHERE tgname LIKE 't%' AND NOT tgisinternal"))
print('[before] rules:', q("SELECT rulename FROM pg_rules WHERE rulename LIKE 'r\\_%' ESCAPE '\\'"))

# 2. 清理所有可能残留
for tbl in ('k_src', 'k_out'):
    q('DROP TABLE IF EXISTS %s' % tbl, fetch=False)
oid = q("SELECT oid FROM pg_class WHERE relname='k_src'")
q("DROP RULE IF EXISTS r_x ON repack.log_999999", fetch=False)  # 幂等兜底
# 遍历 repack.log_* 清理
rows = q("SELECT tablename FROM pg_tables WHERE schemaname='repack' AND tablename LIKE 'log\\_%' ESCAPE '\\'")
for (t,) in (rows or []):
    print('[drop repack table]', t)
    q('DROP TABLE IF EXISTS repack.%s' % t, fetch=False)
rows = q("SELECT typname FROM pg_type WHERE typname LIKE 'pk\\_%' ESCAPE '\\'")
for (t,) in (rows or []):
    print('[drop repack type]', t)
    q('DROP TYPE IF EXISTS repack.%s CASCADE' % t, fetch=False)
q('DROP EXTENSION IF EXISTS dblink', fetch=False)
q('DROP EXTENSION IF EXISTS pg_repack', fetch=False)

# 3. 复查
print('[after] public tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('[after] repack objects:', q("SELECT tablename FROM pg_tables WHERE schemaname='repack'"))
print('[after] types:', q("SELECT typname FROM pg_type WHERE typname LIKE 'pk\\_%' ESCAPE '\\'"))
print('[after] extensions:', q("SELECT extname FROM pg_extension"))
conn.close()
