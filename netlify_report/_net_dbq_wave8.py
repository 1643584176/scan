# -*- coding: utf-8 -*-
"""Netlify database 面收尾:物理复制直连验证 + REST branches 子资源探活
Z1 psycopg replication=database 直连(rolreplication 特性;proxy 是否放行)
Z2 REST POST branches(Netlify Neon branch 特性)
"""
import sys, os, json, re, http.client, ssl
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

# 拿连接串(解析 host/pw,不外显)
conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
conn.request('GET', '/api/v1/sites/%s/database' % SITE_ID, headers={'Authorization': AUTH_HEADER, 'Accept': 'application/json'})
r = conn.getresponse()
d = json.loads(r.read().decode('utf-8', 'replace'))
conn.close()
cs = d.get('connection_strings', {}).get('netlifydb_owner', '')
m = re.search(r'postgresql://netlifydb_owner:([^@]+)@([^/]+)/(\w+)', cs)
PW, HOST, DB = m.group(1), m.group(2), m.group(3)

# Z1: replication 直连
import psycopg
try:
    c = psycopg.connect(host=HOST, port=5432, dbname=DB, user='netlifydb_owner', password=PW,
                        sslmode='require', connect_timeout=10, replication='database', autocommit=True)
    print('Z1_replication: CONNECTED')
    try:
        cur = c.execute('IDENTIFY_SYSTEM')
        print('Z1 identify:', cur.fetchall())
    except Exception as e:
        print('Z1 identify ERR:', str(e)[:200])
    c.close()
except Exception as e:
    print('Z1_replication: FAIL', str(e)[:300])

# Z2: REST branches 探活
def api(method, path, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'Authorization': AUTH_HEADER, 'Accept': 'application/json'}
    data = None
    if body is not None:
        h['Content-Type'] = 'application/json'
        data = json.dumps(body).encode()
    conn.request(method, path, body=data, headers=h)
    r = conn.getresponse()
    raw = r.read()
    conn.close()
    return r.status, raw[:500].decode('utf-8', 'replace')

for tag, method, path in [
    ('Z2a_branches_list', 'GET', '/api/v1/sites/%s/database/branches' % SITE_ID),
    ('Z2b_db_sub_resources', 'GET', '/api/v1/sites/%s/database/roles' % SITE_ID),
]:
    try:
        s, b = api(method, path)
        print('%-24s [%d] %s' % (tag, s, b[:300]))
    except Exception as e:
        print('%-24s ERR %s' % (tag, str(e)[:100]))
