# -*- coding: utf-8 -*-
"""查 anon 含 label 字符串函数源码 + masking 表达式解析逻辑"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
BR3 = 'br-rapid-lake-w2aky5fq'

def req(path):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('GET', API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            return r.status, raw
        except Exception as e:
            time.sleep(2)
    return None, None

st, raw = req('/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s' % (P, BR3))
uri = json.loads(raw).get('uri', '')
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
parts = urlsplit(uri)
q = [(k, v) for k, v in parse_qsl(parts.query) if k != 'channel_binding']
uri = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

import psycopg
with psycopg.connect(uri, connect_timeout=20) as conn:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""select n.nspname, p.proname, p.prosrc
        from pg_proc p join pg_namespace n on n.oid=p.pronamespace
        where n.nspname='anon' and p.prosrc like '%label%'
        order by p.proname""")
    for row in cur.fetchall():
        print('==', row[0], row[1])
        print(row[2][:3000])
        print('---')
