# -*- coding: utf-8 -*-
"""检查残留 + 完整错误输出的重试调试"""
import psycopg, sys

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else None
    except Exception as e:
        return 'ERR: %s' % str(e)[:300]

# 现状
print('tables:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
print('ext:', q("SELECT extname FROM pg_extension"))
print('funcs k_evil:', q("SELECT proname FROM pg_proc WHERE proname='k_evil'"))
print('repack schema:', q("SELECT nspname FROM pg_namespace WHERE nspname='repack'"))

# 清理残留
print('drop k_src:', q("DROP TABLE IF EXISTS k_src", fetch=False))
print('drop k_evil:', q("DROP FUNCTION IF EXISTS k_evil()", fetch=False))
print('after:', q("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
conn.close()
