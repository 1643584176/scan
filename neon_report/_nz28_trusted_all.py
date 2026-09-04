# -*- coding: utf-8 -*-
"""br3: pg_trusted_functions 全表 + pg_masking_rules 完整定义(masking_filter 来源)"""
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
    # 1) trusted 全表 (schema/function 统计)
    cur.execute('select schema, count(*) from anon.pg_trusted_functions group by 1 order by 2 desc')
    print('-- trusted funcs by schema:')
    for row in cur.fetchall():
        print('  ', row)
    cur.execute('select * from anon.pg_trusted_functions limit 30')
    print('-- sample:')
    for row in cur.fetchall():
        print('  ', row)
    # 2) 非 anon schema 的 trusted 函数 (关键!)
    cur.execute("""select schema, function from anon.pg_trusted_functions
        where schema not in ('anon', 'public')""")
    print('-- non-anon trusted:')
    for row in cur.fetchall():
        print('  ', row)
    # 3) masking_rules 视图完整源码 (masking_filter)
    cur.execute("select pg_get_viewdef('anon.pg_masking_rules'::regclass, true)")
    print('-- pg_masking_rules full def (tail):')
    print(cur.fetchone()[0][-3000:])
