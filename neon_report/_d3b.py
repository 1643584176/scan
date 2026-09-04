# -*- coding: utf-8 -*-
"""neonauth 域名探测 + PG neon_auth schema + SDK keys + data-api 联动"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(method, path, body=None, tmo=25):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

# A) neonauth HTTP 探测
def na_get(path, hdrs=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if hdrs: h.update(hdrs)
        conn.request('GET', path, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status
        hd = dict(r.getheaders())
        ct = hd.get('Content-Type', '')
        conn.close()
        return st, ct, raw[:400]
    except Exception as e:
        return 0, '', str(e).encode()[:200]

for p in ['/neondb/auth/.well-known/jwks.json', '/neondb/auth/.well-known/openid-configuration',
          '/neondb/auth/', '/neondb/auth/session', '/neondb/auth/health', '/']:
    st, ct, raw = na_get(p)
    print('\n[NA GET %s] -> %d ct=%s' % (p, st, ct), flush=True)
    print('   ', raw[:300].decode(errors='replace'), flush=True)
    time.sleep(0.8)

# B) PG neon_auth schema
import psycopg
try:
    conn = psycopg.connect('postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb', connect_timeout=20)
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname IN ('neon_auth','auth') ORDER BY 1")
    print('\n[PG neon_auth/auth tables]:', cur.fetchall(), flush=True)
    cur.execute("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'neon%' OR nspname='auth'")
    print('[PG namespaces]:', cur.fetchall(), flush=True)
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE '%neon%' OR rolname LIKE '%auth%' ORDER BY 1")
    print('[PG auth roles]:', cur.fetchall(), flush=True)
    conn.close()
except Exception as e:
    print('[PG err]', e, flush=True)

# C) SDK keys
st, raw = req('POST', '/projects/auth/keys', {'project_id': P, 'auth_provider': 'better_auth'})
print('\n[SDK keys] -> %d' % st, flush=True)
print('   ', raw[:600].decode(errors='replace'), flush=True)

# D) data-api 联动
st, raw = req('GET', '/projects/%s/branches/%s/data-api/neondb' % (P, 'br-wandering-field-w2ob6mpn'))
print('\n[data-api now] -> %d' % st, flush=True)
print('   ', raw[:800].decode(errors='replace'), flush=True)
