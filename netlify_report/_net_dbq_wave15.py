# -*- coding: utf-8 -*-
"""波15:CREATE EXTENSION 矩阵(owner 预装扩展 -> owner 能否自装?区分 permission/not available)
先打印 allowed 全列表,再逐个尝试高价值扩展
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, timeout=60):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'query', 'sql': sql}
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
    return st, raw[:500].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# F0: allowed 全列表
s, b, dt = q("select setting from pg_settings where name = 'neon.allowed_extensions'")
lst = []
try:
    lst = json.loads(b)[0]['setting'].split(',')
except Exception:
    pass
print('F0 allowed total:', len(lst))
print('  ', ','.join(lst))

# F1: CREATE EXTENSION 矩阵(高价值/文件读/出网/后台)
targets = ['file_fdw', 'adminpack', 'pg_duckdb', 'pg_cron', 'pageinspect',
           'pg_buffercache', 'pg_prewarm', 'amcheck', 'pg_repack', 'pg_net',
           'pgvector', 'pgcrypto', 'hstore', 'citext', 'pg_trgm', 'uuid-ossp']
for ext in targets:
    s, b, dt = q("create extension if not exists %s" % ext)
    print('F1 create %-16s [%d] %.1fs %s' % (ext, s, dt, b[:150]))
