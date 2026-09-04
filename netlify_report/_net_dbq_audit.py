# -*- coding: utf-8 -*-
"""巡检:确认提权链实验零残留(只读,无任何副作用)
F1 public 下 k_ 前缀对象 / repack 下 log_/pk_ 对象
F2 k_ 前缀函数 / 触发器
F3 我们自装扩展清单(波15)
F4 库中是否有任何非系统表被改动过(仅列 user 表确认无 k_ 残留)
"""
import http.client, ssl, gzip, brotli, json, sys, time
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


# F1: 残留对象巡检(表/类型/函数/触发器)
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
print('F1_residue       [%d] %.1fs' % (s, dt))
print('   ' + b[:2500])
print()

# F2: public 现有表(确认无 k_ 且看库原本有什么)
s, b, dt = tx(["select tablename from pg_tables where schemaname='public' order by tablename"])
print('F2_public_tables [%d] %.1fs' % (s, dt))
print('   ' + b[:2500])
print()

# F3: 已安装扩展(波15 自装清单)
s, b, dt = tx(["select extname, extversion from pg_extension order by extname"])
print('F3_extensions    [%d] %.1fs' % (s, dt))
print('   ' + b[:2500])
