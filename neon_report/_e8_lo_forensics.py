# -*- coding: utf-8 -*-
"""8 个大对象溯源(纯只读):owner/ACL/大小/内容头"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

print('=== [1] 大对象 metadata ===')
cur.execute("""SELECT m.oid, pg_get_userbyid(m.lomowner) AS owner, m.lomacl::text,
                      COALESCE(sum(length(l.data)),0) AS bytes
               FROM pg_largeobject_metadata m
               LEFT JOIN pg_largeobject l ON l.loid=m.oid
               GROUP BY m.oid, m.lomowner, m.lomacl ORDER BY m.oid""")
rows = cur.fetchall()
for r in rows:
    print(r)

print('\n=== [2] 尝试读取(owner 非 neondb_owner 的,测 ACL) ===')
for oid, owner, acl, _ in rows:
    if owner == 'neondb_owner':
        continue
    try:
        cur.execute('SELECT convert_from(lo_get(%s), %s)', (oid, 'UTF8'))
        print('loid=%s owner=%s -> %s' % (oid, owner, str(cur.fetchone())[:300]))
    except Exception as e:
        print('loid=%s owner=%s ERR: %s' % (oid, owner, str(e)[:150]))

print('\n=== [3] 大对象数据块分布(判断是否真数据) ===')
cur.execute("""SELECT l.loid, count(*) AS pages, min(l.pageno), max(l.pageno)
               FROM pg_largeobject l GROUP BY l.loid ORDER BY l.loid""")
for r in cur.fetchall():
    print(r)

conn.close()
