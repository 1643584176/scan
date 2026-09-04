# -*- coding: utf-8 -*-
"""neon_auth 深挖:表结构 + user 表 email(判断是否 console 账号体系)
不拉取 session token/jwks 密钥内容(敏感)。只读。"""
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

# 1. user 表结构 + email 列表(判断账号体系)
print('=== user table cols ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
          FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
          WHERE c.relname='user' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))
print('\n=== user emails ===')
print(q('SELECT id, email, created_at FROM neon_auth."user"'))

# 2. session 表结构(列名——不拉 token 值)
print('\n=== session cols ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
          FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
          WHERE c.relname='session' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))

# 3. jwks 表结构
print('\n=== jwks cols ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
          FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
          WHERE c.relname='jwks' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))

# 4. account 表结构
print('\n=== account cols ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
          FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
          WHERE c.relname='account' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))
print('\naccount emails:', q('SELECT email, provider FROM neon_auth.account LIMIT 10'))

# 5. project_config 内容(结构信息,不含 secret)
print('\n=== project_config cols ===')
print(q("""SELECT a.attname, format_type(a.atttypid, a.atttypmod)
          FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
          WHERE c.relname='project_config' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum"""))

conn.close()
