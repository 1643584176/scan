# -*- coding: utf-8 -*-
"""修复 _pg15 清理:按依赖序删除残留(k_src / k_rulefn2 / repack.log2_<oid> 等)"""
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
        return 'ERR: %s' % str(e)[:250]

oid = 32935  # k_src 的 oid(从 _pg15 输出)

print('=== 清理前 ===')
print('public tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('repack schema objs:', q("SELECT tablename FROM pg_tables WHERE schemaname='repack'"))
print('k_rulefn2:', q("SELECT proname FROM pg_proc WHERE proname LIKE 'k\\_%'"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))

# 按依赖序:先删引用 k_src 的 repack 日志表 → k_src → pk 类型 → 函数 → 扩展
print('drop log tables:', q("DROP TABLE IF EXISTS repack.log_%d, repack.log2_%d" % (oid, oid), fetch=False))
print('drop k_src:', q("DROP TABLE IF EXISTS k_src", fetch=False))
print('drop pk type:', q("DROP TYPE IF EXISTS repack.pk_%d" % oid, fetch=False))
print('drop k_rulefn2:', q("DROP FUNCTION IF EXISTS k_rulefn2()", fetch=False))
print('drop ext:', q("DROP EXTENSION IF EXISTS pg_repack", fetch=False))

print('=== 清理后 ===')
print('public tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('repack schema exists:', q("SELECT nspname FROM pg_namespace WHERE nspname='repack'"))
print('k_rulefn2:', q("SELECT proname FROM pg_proc WHERE proname LIKE 'k\\_%'"))
print('ext:', q("SELECT extname FROM pg_extension WHERE extname='pg_repack'"))
conn.close()
