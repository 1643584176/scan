# -*- coding: utf-8 -*-
"""postgres 库内容挖掘 + 权限边界
1. health_check/lakebase_attributes 内容
2. neon_migration schema 对象
3. readonly 的 pg_* 成员(postgres 库可读性)
4. postgres 库 CREATE EXTENSION pg_cron(边界确认)
5. neon 视图样例(找敏感字段)"""
import psycopg

A_EP = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'


def get_conn(db='postgres', user='netlifydb_owner', pwd='npg_MtTpnyk2LE4j'):
    return psycopg.connect(host=A_EP, port=5432, user=user, password=pwd, dbname=db,
                           connect_timeout=10, sslmode='require')


def show(conn, label, sql, n=30):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        print('==== %s (%d rows) cols=%s ====' % (label, len(rows), cols))
        for r in rows[:n]:
            print(' ', str(r)[:400])
    except Exception as e:
        print('==== %s ERR %s ====' % (label, str(e).strip()[:250]))
    print()


c = get_conn()
show(c, 'health_check 内容', 'select * from public.health_check')
show(c, 'health_check 行数', 'select count(*) from public.health_check')
show(c, 'lakebase_attributes', 'select * from public.lakebase_attributes limit 20')
show(c, 'lakebase_attributes 计数', 'select count(*) from public.lakebase_attributes')
show(c, 'neon_migration 对象', "select c.relname, c.relkind from pg_class c join pg_namespace n "
     "on c.relnamespace=n.oid where n.nspname='neon_migration' order by 2,1")
show(c, 'neon_migration 内容尝试', 'select * from neon_migration.xxx', n=5)
show(c, 'neon 视图字段', "select viewname from pg_views where schemaname='neon'")
show(c, 'neon_stat_file_cache', 'select * from neon.neon_stat_file_cache limit 10')
show(c, 'neon_lfc_stats', 'select * from neon.neon_lfc_stats limit 10')
show(c, 'neon_perf_counters', 'select * from neon.neon_perf_counters limit 10')
show(c, 'neon_wait_event_snapshot', 'select * from neon.neon_wait_event_snapshot limit 10')
c.close()

print('######## readonly 视角 ########')
cr = get_conn(user='netlifydb_readonly', pwd='WCtJ-h-b7w82YMIaM598M75SV7uYVTCv')
show(cr, 'readonly 成员', "select r.rolname from pg_roles r where pg_has_role('netlifydb_readonly', r.oid, 'member') "
     "and r.rolname not like 'pg\\_%'")
show(cr, 'readonly 读 health_check', 'select * from public.health_check')
show(cr, 'readonly 读 lakebase', 'select * from public.lakebase_attributes limit 5')
cr.close()

print('######## 写权限边界(postgres 库)########')
c2 = get_conn()
show(c2, 'CREATE EXTENSION pg_cron', 'create extension if not exists pg_cron')
show(c2, 'CREATE TABLE public', 'create table if not exists public.k_x(id int)')
show(c2, 'CREATE SCHEMA k_s', 'create schema if not exists k_s')
show(c2, 'SELECT into 测试', 'create table k_t as select 1 as x')
show(c2, 'TEMP 表', 'create temp table k_tt(id int)')
c2.close()
