# -*- coding: utf-8 -*-
"""清理 _pg11/_pg13 残留的 k_evil 函数 + 终验"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

cur.execute('DROP FUNCTION IF EXISTS k_evil()')
cur.execute("SELECT proname FROM pg_proc WHERE proname LIKE 'k\\_%'")
print('remaining k_* funcs:', cur.fetchall())
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname IN ('public','repack')")
print('tables public/repack:', cur.fetchall())
cur.execute("SELECT extname FROM pg_extension WHERE extname='pg_repack'")
print('pg_repack:', cur.fetchall())
conn.close()
