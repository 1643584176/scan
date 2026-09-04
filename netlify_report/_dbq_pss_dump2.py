# -*- coding: utf-8 -*-
"""重装 pg_stat_statements(统计在共享内存,drop 不丢)→ dump cloud_admin 语句"""
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


st, out = q('create extension if not exists pg_stat_statements')
print('install [%d] %s' % (st, out[:150]))
print()
print('== cloud_admin 非健康检查语句 ==')
st, out = q("select dbid, queryid, left(query, 700) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid=5 "
            "and not (query ilike '%pg_stat_activity%' or query ilike '%pg_stat_replication%' "
            "or query ilike '%pg_stat_subscription%' or query ilike '%pg_is_in_recovery%' "
            "or query ilike '%pg_current_wal_lsn%' or query ilike '%pg_stat_database%' "
            "or query ilike '%neon_lfc%' or query ilike '%neon_perf%' or query ilike '%pg_replication_slots%') "
            "order by calls desc limit 80")
print('[%d] %s' % (st, out[:3000]))
print()
print('== cloud_admin dbid=1 ==')
st, out = q("select dbid, left(query, 1000) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid=1")
print('[%d] %s' % (st, out[:2000]))
print()
print('== cloud_admin netlifydb 库(dbid=16396)==')
st, out = q("select left(query, 800) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid=16396")
print('[%d] %s' % (st, out[:1500]))
