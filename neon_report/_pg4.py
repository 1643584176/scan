# -*- coding: utf-8 -*-
"""pg_session_jwt 机制 + Data API Bearer 认证矩阵"""
import psycopg, http.client, ssl, json, sys
ctx = ssl.create_default_context()
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
cred = json.load(open(r'D:\scan\neon_report\_cred.json')) if __import__('os').path.exists(r'D:\scan\neon_report\_cred.json') else None

HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@%s/neondb' % HOST
conn = psycopg.connect(URI, connect_timeout=30)
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        return [('ERR', str(e)[:200])]

print('[1] auth func signatures:')
for f in ['jwt', 'jwt_session_init', 'uid', 'user_id', 'organization_id', 'session', 'init']:
    print('   ', q("SELECT pg_get_function_identity_arguments(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='auth' AND p.proname='%s'" % f))

print('[2] auth.jwt() now:', q('SELECT auth.jwt()'))
print('[3] auth.uid() now:', q('SELECT auth.uid()'))
print('[4] auth.organization_id():', q('SELECT auth.organization_id()'))
print('[5] jwt_session_init args check:', q("SELECT p.proargnames, pg_get_function_arguments(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='auth' AND p.proname='jwt_session_init'"))
conn.close()

# Data API Bearer 矩阵
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
BASE = '/neondb/rest/v1'
tokens = {'apikey(napi)': key, 'none': None}
if cred:
    tokens['cred.api_token'] = cred.get('api_token')
    tokens['cred.token_id'] = cred.get('token_id')

def get(path, tok):
    try:
        conn = http.client.HTTPSConnection(DA, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if tok: h['Authorization'] = 'Bearer ' + tok
        conn.request('GET', BASE + path, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw[:300]
    except Exception as e:
        return 0, str(e).encode()

for name, tok in tokens.items():
    for p in ['/', '/openapi.json']:
        st, raw = get(p, tok)
        print('\n== DA %s Bearer[%s] GET %s -> %d' % (name, (tok or '')[:10], p, st))
        print('   ', raw[:250])
