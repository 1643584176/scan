# -*- coding: utf-8 -*-
"""低频段 query 全量过目 + pg_export_snapshot 影响确认"""
import psycopg

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI_PG = 'postgresql://neondb_owner:%s@%s/postgres' % (PWD, HOST)

c = psycopg.connect(URI_PG, connect_timeout=20)
c.autocommit = True
cur = c.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== 低频段 query(1-30 calls,全量过目) ===')
rows = q("""SELECT calls, (SELECT rolname FROM pg_roles WHERE oid=userid) AS usr, query
            FROM pg_stat_statements WHERE calls <= 30 ORDER BY calls DESC""")
seen = set()
for r in rows or []:
    # 跳过已归档的启动脚本类
    t = r[2] or ''
    if t in seen: continue
    seen.add(t)
    first = ' '.join(t.split())[:170]
    print('calls=%3s %-16s %s' % (r[0], r[1], first))

print('\n=== pg_export_snapshot 语义确认(租户面) ===')
print('能否导出快照(neondb_owner):', q("SELECT pg_export_snapshot()"))

print('\n=== lakebase_attributes 其他潜在消费方(全库函数 grep) ===')
print(q("""SELECT n.nspname, p.proname, l.lanname
           FROM pg_proc p
           JOIN pg_namespace n ON n.oid=p.pronamespace
           JOIN pg_language l ON l.oid=p.prolang
           WHERE p.prosrc LIKE '%%lakebase_attributes%%' OR p.prosrc LIKE '%%primary_memory%%'
           ORDER BY 1,2"""))

print('\n=== lakebase_attributes 的写入者线索: 全量 query 含 lakebase 的 ===')
print(q("""SELECT calls, (SELECT rolname FROM pg_roles WHERE oid=userid), query
           FROM pg_stat_statements WHERE query LIKE '%%lakebase%%'"""))

c.close()
