# -*- coding: utf-8 -*-
"""源分支建探针: 函数记录调用者身份到 log 表 (验证脱敏作业执行角色)"""
import http.client, ssl, json, time, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'

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

st, raw = req('/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner' % P)
uri = json.loads(raw).get('uri', '')
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
parts = urlsplit(uri)
q = [(k, v) for k, v in parse_qsl(parts.query) if k != 'channel_binding']
uri = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

import psycopg
with psycopg.connect(uri, connect_timeout=20) as conn:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('drop table if exists public.sbx_probe_log')
    cur.execute('drop function if exists public.sbx_probe_fn(text)')
    cur.execute('''create table public.sbx_probe_log (
        id bigint generated always as identity primary key,
        ts timestamptz default now(), cur_user text, ses_user text,
        rolsuper bool, tries text)''')
    cur.execute('''create function public.sbx_probe_fn(_in text)
        returns text language plpgsql volatile as $f$
        declare r record; out text;
        begin
            select current_user, session_user into out from (select 1) x;
            insert into public.sbx_probe_log (cur_user, ses_user)
            select current_user::text, session_user::text;
            -- 尝试读 pg_authid 的 rolsuper 标志(记录是否成功)
            begin
                select rolsuper into r from pg_roles where rolname = current_user;
                update public.sbx_probe_log set rolsuper = r.rolsuper
                where id = (select max(id) from public.sbx_probe_log);
            exception when others then
                update public.sbx_probe_log set tries = SQLERRM
                where id = (select max(id) from public.sbx_probe_log);
            end;
            return 'probe:' || out;
        end $f$''')
    cur.execute('grant execute on function public.sbx_probe_fn(text) to public')
    cur.execute('grant select, insert, update on public.sbx_probe_log to public')
    # 自测一次(应以 neondb_owner 执行)
    cur.execute("select public.sbx_probe_fn('x')")
    print('self-call:', cur.fetchone())
    cur.execute('select id, cur_user, ses_user, rolsuper, tries from public.sbx_probe_log order by id')
    print('log:', cur.fetchall())
print('probe ready')
