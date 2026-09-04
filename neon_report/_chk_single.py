# -*- coding: utf-8 -*-
"""只读:当前 project 列表 + PG 残留检查(demo_rls/jwks 清理确认)"""
import psycopg, json, http.client, ssl, sys

sys.path.insert(0, '.')
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
key = json.load(open('_apikey.json', encoding='utf-8'))['key']

def req(method, path, tmo=20):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

st, raw = req('GET', '/projects')
print('[projects] ->', st)
print(raw.decode(errors='replace')[:2000])

# PG 残留检查
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
try:
    conn = psycopg.connect(URI, connect_timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.demo_rls')")
    print('demo_rls exists:', cur.fetchone()[0])
    cur.execute('SELECT count(*), max("createdAt") FROM neon_auth.jwks')
    print('jwks rows:', cur.fetchone())
    cur.execute("SELECT to_regclass('public.auth_integration_probe')")
    print('probe exists:', cur.fetchone()[0])
    conn.close()
except Exception as e:
    print('PG err:', e)
