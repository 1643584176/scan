# -*- coding: utf-8 -*-
"""B 库残留修复:reproB 清理链因先拆 log 触发器而断链,k_run/k_pwned(owner=cloud_admin)残留
方案:借 k_run(security definer, owner=cloud_admin)以 cloud_admin 执行
  alter owner -> netlifydb_owner,然后普通权限 drop
步骤:C0 借 k_run 转移 owner -> C1 drop 两者 -> C2 复巡检零残留
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=60):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_B,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_B, 'action': 'transaction', 'queries': [{'sql': x} for x in qs]}
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


# C0: 借 k_run 以 cloud_admin 转移 owner
s, b, dt = tx([
    "select * from public.k_run('alter table public.k_pwned owner to netlifydb_owner')",
    "select * from public.k_run('alter function public.k_run(text) owner to netlifydb_owner')",
])
print('C0_transfer      [%d] %.1fs' % (s, dt))
print('   ' + b[:600])

# C1: 普通权限 drop
s, b, dt = tx([
    "select tableowner from pg_tables where tablename='k_pwned'",
    "select p.proname, r.rolname from pg_proc p "
    "join pg_roles r on p.proowner=r.oid where p.proname='k_run'",
])
print('C1a_checkowner   [%d] %.1fs' % (s, dt))
print('   ' + b[:600])

s, b, dt = tx([
    "drop table if exists public.k_pwned",
    "drop function if exists public.k_run(text)",
])
print('C1b_drop         [%d] %.1fs' % (s, dt))
print('   ' + b[:600])

# C2: 复巡检(与 reproB R6 同口径)
s, b, dt = tx([
    "select 'rel' as t, n.nspname||'.'||c.relname as nm from pg_class c "
    "join pg_namespace n on c.relnamespace=n.oid "
    "where (n.nspname='public' and c.relname like 'k\\_%') "
    "or (n.nspname='repack' and (c.relname like 'log\\_%' or c.relname like 'pk\\_%'))",
    "select 'fun' as t, n.nspname||'.'||p.proname as nm from pg_proc p "
    "join pg_namespace n on p.pronamespace=n.oid where p.proname like 'k\\_%'",
    "select 'trg' as t, t.tgrelid::regclass::text||' . '||t.tgname as nm from pg_trigger t "
    "where t.tgname like 'k\\_%' and not t.tgisinternal",
    "select extname from pg_extension where extname='pg_repack'",
    "select 'schema' as t, count(*) from pg_namespace where nspname='repack'",
])
print('C2_residue       [%d] %.1fs' % (s, dt))
print('   ' + b[:1000])
