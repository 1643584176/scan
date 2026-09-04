# -*- coding: utf-8 -*-
"""实测:CREATE EXTENSION pg_repack 在 Neon 是否可行 + 结果 owner 审计(成功后立即查,可回滚 DROP)"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

# 1) 尝试创建(受控;若成功下面查清楚后 DROP)
try:
    cur.execute('CREATE EXTENSION IF NOT EXISTS pg_repack VERSION "1.5.2"')
    print('[create] OK')
except Exception as e:
    print('[create] DENIED:', str(e)[:300])
    conn.close()
    raise SystemExit

# 2) 扩展 owner
cur.execute("SELECT e.extname, pg_get_userbyid(e.extowner) FROM pg_extension e WHERE extname='pg_repack'")
print('ext owner:', cur.fetchone())

# 3) repack schema + ACL
cur.execute("SELECT nspname, pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='repack'")
print('repack schema:', cur.fetchone())
cur.execute("""SELECT COALESCE(ARRAY_TO_STRING(ARRAY(
    SELECT grantee::regrole::text || ':' || privilege_type
    FROM aclexplode(COALESCE(nspacl, acldefault('n', nspowner)))
    WHERE grantee::regrole::text IN ('neondb_owner','cloud_admin','neon_superuser','neon_service','PUBLIC')
    ), ','), '(default)') FROM pg_namespace n WHERE nspname='repack'""")
print('repack nspacl:', cur.fetchone())

# 4) 函数 owner + definer 面
cur.execute("""SELECT p.proname, pg_get_userbyid(p.proowner), p.prosecdef
   FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='repack' ORDER BY 1""")
print('repack funcs:')
for r in cur.fetchall():
    print('  ', r)

# 5) 表/触发器
cur.execute("""SELECT relname, pg_get_userbyid(relowner) FROM pg_class c
   JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='repack' AND relkind IN ('r','v') ORDER BY 1""")
print('repack rels:')
for r in cur.fetchall():
    print('  ', r)

# 6) 尝试 SET ROLE 到扩展 owner 看看能力边界(仅信息)
for rn in ['neon_service', 'cloud_admin', 'neon_superuser']:
    try:
        cur.execute('SET ROLE %s' % rn)
        cur.execute('SELECT current_user')
        print('SET ROLE %s -> OK %s' % (rn, cur.fetchone()[0]))
        cur.execute('RESET ROLE')
    except Exception as e:
        print('SET ROLE %s -> DENIED %s' % (rn, str(e)[:100]))
        try:
            cur.execute('RESET ROLE')
        except Exception:
            pass
conn.close()
