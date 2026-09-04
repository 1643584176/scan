# -*- coding: utf-8 -*-
"""波13:跨库组合链——连 postgres 库(cron/TimescaleDB/扩展)+ pg_authid ACL 确认
D1 postgres 库扩展 / D2 cron.job 存在性+ACL / D3 cron schema 函数 / D4 timescaledb / D5 pg_authid ACL
"""
import sys, re, json, http.client, ssl
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
conn.request('GET', '/api/v1/sites/%s/database' % SITE_ID, headers={'Authorization': AUTH_HEADER, 'Accept': 'application/json'})
r = conn.getresponse()
d = json.loads(r.read().decode('utf-8', 'replace'))
conn.close()
cs = d.get('connection_strings', {}).get('netlifydb_owner', '')
m = re.search(r'postgresql://netlifydb_owner:([^@]+)@([^/]+)/(\w+)', cs)
PW, HOST, DB = m.group(1), m.group(2), m.group(3)
print('conn:', HOST, DB)

import psycopg

probes = [
    ('D1_extensions',     "select extname, extowner::regrole::text from pg_extension"),
    ('D2_cron_job',       "select to_regclass('cron.job') as job, to_regclass('cron.schedule') as sched"),
    ('D2b_cron_acl',      "select c.relname, coalesce(array_to_string(c.relacl::text[], ','), 'NULL') as acl from pg_class c where c.relname in ('job', 'schedule', 'job_run_details') and c.relnamespace = (select oid from pg_namespace where nspname='cron')"),
    ('D3_cron_funcs',     "select p.proname, pg_get_function_identity_arguments(p.oid) as args from pg_proc p where p.pronamespace = (select oid from pg_namespace where nspname='cron') order by p.proname"),
    ('D4_timescale',      "select extname from pg_extension where extname like '%timescale%'"),
    ('D4b_ts_funcs',      "select count(*) as n from pg_proc p where p.pronamespace = (select oid from pg_namespace where nspname='_timescaledb_internal')"),
    ('D5_authid_acl',     "select relacl::text from pg_class where relname = 'pg_authid'"),
    ('D6_my_roles',       "select current_user, (select rolsuper from pg_roles where rolname=current_user) as super"),
]


def run(conn, label, sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            cols = [d.name for d in cur.description] if cur.description else []
            print('%-16s' % label, rows[:5])
            if len(rows) > 5:
                print('  ... total %d rows' % len(rows))
    except Exception as e:
        print('%-16s ERR: %s' % (label, str(e)[:250]))


for dbname in ('postgres', 'netlifydb'):
    print('===== dbname = %s =====' % dbname)
    try:
        c = psycopg.connect(host=HOST, port=5432, dbname=dbname, user='netlifydb_owner', password=PW,
                            sslmode='require', connect_timeout=10)
        c.autocommit = True
        for label, sql in probes:
            run(c, label, sql)
        c.close()
    except Exception as e:
        print('connect ERR:', str(e)[:300])
