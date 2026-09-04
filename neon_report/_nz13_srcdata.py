# -*- coding: utf-8 -*-
"""拿 neondb_owner 连接串 -> 建源数据表 sbx_anon_src"""
import http.client, ssl, json, time, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            return r.status, raw
        except Exception as e:
            time.sleep(2)
    return None, None

st, raw = req('uri', '/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner' % P)
print('uri ->', st, raw[:400])
uri = json.loads(raw).get('uri', '')
print('URI:', uri.replace(uri.split('@')[0].split('://')[1], '***') if '@' in uri else uri)

# 建表+插数据
import psycopg
try:
    with psycopg.connect(uri, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute('drop table if exists public.sbx_anon_src')
            cur.execute('''create table public.sbx_anon_src (
                id bigint generated always as identity primary key,
                email text not null, full_name text not null, secret text not null,
                phone text, created_at timestamptz default now())''')
            cur.execute("""insert into public.sbx_anon_src (email, full_name, secret, phone) values
                ('alice@victim.com', 'Alice Victim', 'tok_sec_alice_9f3a', '+1-555-0101'),
                ('bob@victim.com', 'Bob Victim', 'tok_sec_bob_77c1', '+1-555-0102'),
                ('carol@victim.com', 'Carol Victim', 'tok_sec_carol_2e8b', '+1-555-0103')""")
        conn.commit()
        with conn.cursor() as cur:
            cur.execute('select id, email, full_name, secret from public.sbx_anon_src order by id')
            print('rows:', cur.fetchall())
    print('source table ready')
except Exception as e:
    print('DB ERR', e)
