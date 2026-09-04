# -*- coding: utf-8 -*-
"""检查 auth3 执行结果:jwks 列表 + PG 角色现状(带 flush)"""
import http.client, ssl, json, sys
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, tmo=15):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

st, raw = req('GET', '/projects/%s/jwks' % P)
print('GET /jwks ->', st, flush=True)
try:
    d = json.loads(raw)
    for j in d.get('jwks', []):
        print('  provider:', j.get('provider_name'), '| url:', j.get('jwks_url'), '| roles:', j.get('role_names'), '| id:', j.get('id'), flush=True)
except Exception as e:
    print(raw[:300], e, flush=True)

# PG 检查是否有注入角色
import psycopg
try:
    conn = psycopg.connect('postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb', connect_timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' ORDER BY 1")
    print('PG roles:', [r[0] for r in cur.fetchall()], flush=True)
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE '%pwn%' OR rolname LIKE '%sec%' OR rolname LIKE '%inject%'")
    print('injected?', cur.fetchall(), flush=True)
    conn.close()
except Exception as e:
    print('PG err:', e, flush=True)
