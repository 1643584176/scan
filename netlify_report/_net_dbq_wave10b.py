# -*- coding: utf-8 -*-
"""BASE_BACKUP 完整错误诊断 + 变体 + 复制命令探测"""
import sys, re, json, http.client, ssl
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

cmds = [
    ("C1", "BASE_BACKUP"),
    ("C2", "BASE_BACKUP LABEL 'x'"),
    ("C3", "IDENTIFY_SYSTEM"),
    ("C4", "SHOW wal_level"),
    ("C5", "SELECT 1"),
]
for tag, cmd in cmds:
    try:
        cur = c.execute(cmd)
        try:
            rows = cur.fetchall()
            print('%-4s OK rows=%s' % (tag, str(rows)[:200]))
        except Exception as e2:
            print('%-4s OK but fetch ERR: %s' % (tag, str(e2)[:200]))
    except Exception as e:
        sev = getattr(e, 'diag', None)
        detail = ''
        if sev is not None:
            detail = ' | severity=%s sqlstate=%s msg=%s' % (sev.severity, sev.sqlstate, sev.message_primary)
        print('%-4s ERR: %s%s' % (tag, str(e)[:200], detail))
c.close()
