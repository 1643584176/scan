# -*- coding: utf-8 -*-
"""技术层测试 5:
1. api.netlify.com 拿 A owner 连接串(确认 dblink 密码)
2. dblink_connect localhost 基线(判断 dblink_connect 是否可用)
3. neon_utils 扩展全部对象(表/函数/视图)
4. lakebase_vector/h3/anon/hypopg/pg_cron 可装性(Neon 白名单边界)"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def api(method, path, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + TOKEN_A}
    data = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=data, headers=h)
    r = conn.getresponse()
    raw = r.read()
    if r.getheader('Content-Encoding') == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out


def q(sql, cookie=None):
    from _net_creds import COOKIE_A
    cookie = cookie or COOKIE_A
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
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
    out = raw[:1800].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def qq(s):
    return "'" + s.replace("'", "''") + "'"


print('== 1. A 连接串(api.netlify.com) ==')
st, out = api('GET', '/api/v1/sites/%s/database' % SITE_A)
print('[%d] %s' % (st, out[:700]))
m = re.search(r'postgres://[^"\s\\]+', out)
pwd_a = None
if m:
    pwd_a = m.group(0).split('@')[0].rsplit(':', 1)[1]
    print('A owner pwd =', pwd_a)

print()
print('== 2. dblink localhost 基线 ==')
if pwd_a:
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': __import__('_net_creds', fromlist=['COOKIE_A']).COOKIE_A}
    cs = 'host=127.0.0.1 port=5432 dbname=netlifydb user=netlifydb_owner password=' + pwd_a
    body = {'siteId': SITE_A, 'action': 'transaction', 'queries': [
        {'sql': 'select dblink_connect(%s, %s)' % (qq('c1'), qq(cs))},
        {'sql': "select * from dblink('c1', %s) as t(u text)" % qq('select current_user::text')},
        {'sql': "select dblink_disconnect('c1')"}]}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    print('localhost base [%d] %s' % (r.status, raw[:400].decode('utf-8', 'ignore')))
    conn.close()

print()
print('== 3. neon_utils 对象清单 ==')
st, out = q("select c.relname||'('||c.relkind||')' from pg_class c join pg_depend d on d.objid=c.oid and d.classid='pg_class'::regclass "
            "join pg_extension e on d.refobjid=e.oid where e.extname='neon_utils' order by 1")
print('[%d] %s' % (st, out[:1200]))
st, out = q("select p.proname from pg_proc p join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
            "join pg_extension e on d.refobjid=e.oid where e.extname='neon_utils' order by 1")
print('neon_utils funcs [%d] %s' % (st, out[:1500]))

print()
print('== 4. 扩展白名单边界 ==')
for ext in ['lakebase_vector', 'h3', 'anon', 'hypopg', 'pg_cron', 'citext', 'uuid-ossp']:
    st, out = q('create extension if not exists ' + ext)
    print('create %-16s [%d] %s' % (ext, st, out[:150]))
