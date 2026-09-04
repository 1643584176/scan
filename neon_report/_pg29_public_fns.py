# -*- coding: utf-8 -*-
"""PUBLIC 可执行函数全清单 + lakebase_attributes 消费方线索(本地 JS + pg_stat_activity 观察)"""
import psycopg

URI2 = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/postgres'
conn = psycopg.connect(URI2, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return 'ERR: %s' % str(e)[:250]

print('=== [1] PUBLIC EXECUTE(proacl IS NULL)的 neon 函数 ===')
print(q("""SELECT p.proname, p.proargnames, p.prorettype::regtype
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='neon' AND p.proacl IS NULL ORDER BY 1"""))

print('=== [2] 有副作用风险函数的 proacl 细查 ===')
for fn in ('replace_hll', 'get_hll_state', 'neon_clear_lfc', 'prewarm_local_cache', 'cancel_prewarm',
           'neon_invalidate_relsize_cache', 'get_local_cache_state', 'neon_emit_reverse_etl_commit',
           'reset_perf_counter', 'pg_resize_shared_buffers'):
    print(' ', fn, q("SELECT proacl FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='neon' AND p.proname='%s'" % fn))

print('=== [3] 当前活动连接(看有无平台进程连本库) ===')
print(q("""SELECT datname, usename, application_name, state, left(query, 80)
  FROM pg_stat_activity WHERE datname IS NOT NULL"""))

print('=== [4] postgres 库最近访问 lakebase_attributes 痕迹 ===')
print(q("SELECT relname, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup FROM pg_stat_user_tables WHERE relname='lakebase_attributes'"))
conn.close()
