# -*- coding: utf-8 -*-
"""br3 本地实验: anon 表/视图结构 + 手动 label + 自定义函数脱敏"""
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
    # anon schema 对象
    cur.execute("""select relname, relkind from pg_class c join pg_namespace n on n.oid=c.relnamespace
        where n.nspname='anon' and relkind in ('r','v','m','S') order by 1""")
    print('-- anon relations:')
    for row in cur.fetchall():
        print('  ', row)
    # 实验1: 简单函数直接 label
    cur.execute('create or replace function public.mk_fn() returns text language sql immutable as $$ select \'M\'::text $$')
    cur.execute('grant execute on function public.mk_fn() to public')
    for fn in ('public.mk_fn()', 'mk_fn()', 'anon.fake_email()'):
        try:
            cur.execute("select pg_catalog.set_config('anon.maskschema','public',false)") if False else None
            cur.execute("SELECT anon.anonymize_table(%s::regclass)", ('public.sbx_anon_src',))
        except Exception:
            pass
        try:
            cur.execute("SECURITY LABEL FOR anon ON COLUMN public.sbx_anon_src.full_name IS %s", ('MASKED WITH FUNCTION ' + fn,))
            print('LABEL OK:', fn)
            cur.execute("SELECT anon.anonymize_table('public.sbx_anon_src')")
            print('ANON OK:', fn)
            cur.execute('select id, full_name from public.sbx_anon_src order by id limit 3')
            print('  data:', cur.fetchall())
            cur.execute("SECURITY LABEL FOR anon ON COLUMN public.sbx_anon_src.full_name IS 'MASKED'")
            # 恢复原值
            cur.execute("update public.sbx_anon_src set full_name = case id when 1 then 'Alice Victim' when 2 then 'Bob Victim' else 'Carol Victim' end")
        except Exception as e:
            print('LABEL FAIL:', fn, '->', str(e).split(chr(10))[0][:200])
