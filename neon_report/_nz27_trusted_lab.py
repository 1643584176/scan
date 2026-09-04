# -*- coding: utf-8 -*-
"""br3: 尝试给自定义函数设 TRUSTED label -> 验证本地 masking 全链"""
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
    # 0) 建探针函数(写日志版)
    cur.execute('drop table if exists public.sbx_probe_log')
    cur.execute('drop function if exists public.sbx_probe_fn()')
    cur.execute('''create table public.sbx_probe_log (id bigint generated always as identity primary key,
        ts timestamptz default now(), cur_user text, ses_user text, rolsuper bool, tries text)''')
    cur.execute('''create function public.sbx_probe_fn() returns text language plpgsql volatile as $f$
        declare out text;
        begin
            out := current_user::text;
            insert into public.sbx_probe_log (cur_user, ses_user)
            select current_user::text, session_user::text;
            begin
                update public.sbx_probe_log set rolsuper =
                    (select rolsuper from pg_roles where rolname = current_user)
                where id = (select max(id) from public.sbx_probe_log);
            exception when others then
                update public.sbx_probe_log set tries = SQLERRM
                where id = (select max(id) from public.sbx_probe_log);
            end;
            return 'probe:' || out;
        end $f$''')
    cur.execute('grant execute on function public.sbx_probe_fn() to public')
    cur.execute('grant select, insert, update on public.sbx_probe_log to public')
    # 1) 设 TRUSTED label
    try:
        cur.execute("SECURITY LABEL FOR anon ON FUNCTION public.sbx_probe_fn() IS 'TRUSTED'")
        print('TRUSTED label OK (as neondb_owner)')
    except Exception as e:
        print('TRUSTED label FAIL:', str(e).split(chr(10))[0][:300])
    cur.execute('select * from anon.pg_trusted_functions where function = %s', ('sbx_probe_fn',))
    print('trusted list check:', cur.fetchall())
    # 2) 设 MASKED WITH FUNCTION
    try:
        cur.execute("SECURITY LABEL FOR anon ON COLUMN public.sbx_anon_src.full_name IS 'MASKED WITH FUNCTION public.sbx_probe_fn()'")
        print('MASK label OK')
    except Exception as e:
        print('MASK label FAIL:', str(e).split(chr(10))[0][:300])
    # 3) 本地触发脱敏
    try:
        cur.execute("select anon.anonymize_table('public.sbx_anon_src')")
        print('anonymize_table OK')
    except Exception as e:
        print('anonymize FAIL:', str(e).split(chr(10))[0][:300])
    cur.execute('select id, cur_user, ses_user, rolsuper, tries from public.sbx_probe_log order by id')
    print('probe log:', cur.fetchall())
    cur.execute('select id, full_name from public.sbx_anon_src order by id')
    print('data:', cur.fetchall())
    # 4) 清 label + 恢复数据
    try:
        cur.execute("SECURITY LABEL FOR anon ON COLUMN public.sbx_anon_src.full_name IS 'MASKED'")
    except Exception:
        pass
    cur.execute("update public.sbx_anon_src set full_name = case id when 1 then 'Alice Victim' when 2 then 'Bob Victim' else 'Carol Victim' end")
    print('cleaned')
