# -*- coding: utf-8 -*-
"""postgres 库面侦察(外部直连,只读)
1. 已装扩展
2. 全部 SECURITY DEFINER 函数
3. schema 清单 + owner + 权限
4. neon schema 对象
5. public schema 权限(owner 能否 CREATE)"""
import psycopg

A_EP = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
conn = psycopg.connect(host=A_EP, port=5432, user='netlifydb_owner',
                       password='npg_MtTpnyk2LE4j', dbname='postgres',
                       connect_timeout=10, sslmode='require')


def show(label, sql, limit=2500):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        print('==== %s (%d rows) ====' % (label, len(rows)))
        for r in rows[:40]:
            s = str(r)
            print(' ', s[:250])
    except Exception as e:
        print('==== %s ERR %s ====' % (label, str(e).strip()[:200]))
    print()


show('已装扩展', "select e.extname, e.extversion, n.nspname from pg_extension e "
     "join pg_namespace n on e.extnamespace=n.oid order by 1")
show('DEFINER 函数', "select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' as fn, "
     "r.rolname as owner from pg_proc p join pg_namespace n on p.pronamespace=n.oid "
     "join pg_roles r on p.proowner=r.oid where p.prosecdef and n.nspname not in ('pg_catalog','information_schema') "
     "order by r.rolname, n.nspname")
show('schema 清单', "select n.nspname, r.rolname as owner, "
     "has_schema_privilege('netlifydb_owner', n.nspname, 'CREATE') as can_create, "
     "has_schema_privilege('netlifydb_owner', n.nspname, 'USAGE') as can_use "
     "from pg_namespace n join pg_roles r on n.nspowner=r.oid "
     "where n.nspname not in ('pg_catalog','information_schema','pg_toast') order by n.nspname")
show('neon schema 对象', "select c.relname, c.relkind, pg_get_userbyid(c.relowner) from pg_class c "
     "join pg_namespace n on c.relnamespace=n.oid where n.nspname='neon' order by 2,1")
show('public 表', "select c.relname, c.relkind, pg_get_userbyid(c.relowner) from pg_class c "
     "join pg_namespace n on c.relnamespace=n.oid where n.nspname='public' order by 2,1 limit 30")
show('netlifydb_owner 成员', "select r.rolname from pg_roles r where pg_has_role('netlifydb_owner', r.oid, 'member') "
     "and r.rolname like 'pg\\_%' or pg_has_role('netlifydb_owner', r.oid, 'member') and r.rolname in ('neon_superuser','cloud_admin')")
show('pg_cron 可用性', "select name, default_version from pg_available_extensions where name in ('pg_cron','pg_repack')")
conn.close()
