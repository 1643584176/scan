# -*- coding: utf-8 -*-
"""postgres 库深度:独立事务修正 + pg_stat_activity/pg_hba_file_rules/migration 内容"""
import psycopg

A_EP = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
conn = psycopg.connect(host=A_EP, port=5432, user='netlifydb_owner',
                       password='npg_MtTpnyk2LE4j', dbname='postgres',
                       connect_timeout=10, sslmode='require', autocommit=True)


def show(label, sql, n=40):
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


show('migration_id 内容', 'select * from neon_migration.migration_id order by 1')
show('neon 视图字段', "select viewname from pg_views where schemaname='neon'")
show('neon_stat_file_cache', 'select * from neon.neon_stat_file_cache limit 15')
show('neon_lfc_stats', 'select * from neon.neon_lfc_stats limit 15')
show('neon_perf_counters', 'select * from neon.neon_perf_counters limit 15')
show('neon_wait_event_snapshot', 'select * from neon.neon_wait_event_snapshot limit 15')

print('############ pg_stat_activity(所有连接)############')
show('活跃连接', "select pid, usename, application_name, client_addr, client_port, state, "
     "left(query,120) as q, backend_type from pg_stat_activity order by backend_start desc limit 30")
show('cloud_admin 连接', "select pid, application_name, client_addr, state, left(query,150) as q "
     "from pg_stat_activity where usename='cloud_admin'")
print('############ pg_hba_file_rules ############')
show('hba 规则', 'select line_number, type, database, user_name, address, netmask, auth_method from pg_hba_file_rules')
print('############ 其他全局信息 ############')
show('pg_stat_database', "select datname, numbackends, xact_commit, blks_read from pg_stat_database")
show('监听端口/目录', "select name, setting from pg_settings where name in ('port','data_directory','unix_socket_directories','listen_addresses','shared_preload_libraries','cluster_name')")
conn.close()
