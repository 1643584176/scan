# -*- coding: utf-8 -*-
"""波16:pg_cron 组合链(跨库+扩展+后台任务)
G1 postgres 库 CREATE EXTENSION pg_cron / G2 cron 对象 ACL / G3 job 表结构
G4 尝试以 username=cloud_admin 插入 job(无害探测:写 current_user 到目标表)
"""
import sys, re, json, time, http.client, ssl
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
PW, HOST = m.group(1), m.group(2)

import psycopg


def run(c, label, sql, fetch=True):
    try:
        with c.cursor() as cur:
            cur.execute(sql)
            if fetch and cur.description:
                rows = cur.fetchall()
                print('%-22s %d rows' % (label, len(rows)))
                for r in rows[:8]:
                    print('     ', r)
            else:
                print('%-22s OK' % label)
    except Exception as e:
        print('%-22s ERR: %s' % (label, str(e)[:250]))


# ============ postgres 库 ============
c = psycopg.connect(host=HOST, port=5432, dbname='postgres', user='netlifydb_owner', password=PW,
                    sslmode='require', connect_timeout=10)
c.autocommit = True
run(c, 'G1_create_cron', "create extension if not exists pg_cron")
run(c, 'G2_cron_tables', "select schemaname, tablename from pg_tables where schemaname='cron'")
run(c, 'G2b_cron_acl', """select c.relname, c.relowner::regrole::text as owner,
       coalesce(array_to_string(c.relacl::text[], ','), 'NULL') as acl
       from pg_class c join pg_namespace n on c.relnamespace = n.oid
       where n.nspname = 'cron' order by c.relname""")
run(c, 'G3_job_cols', """select column_name, data_type from information_schema.columns
       where table_schema='cron' and table_name='job' order by ordinal_position""")
c.close()
