# -*- coding: utf-8 -*-
"""清理 sec3-* provider + 确认 cloud_admin 拒绝原因 + DROP 畸形角色"""
import http.client, ssl, json, sys
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, tmo=20):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

st, raw = req('GET', '/projects/%s/jwks' % P)
jwks = json.loads(raw).get('jwks', [])

# 1) 删 sec3-* 与 sec2-google j(全清,之后需要再建)
for j in jwks:
    nm = j.get('provider_name', '')
    if nm.startswith('sec') or nm.startswith('sec2') or nm.startswith('sec3'):
        st, raw = req('DELETE', '/projects/%s/jwks/%s' % (P, j['id']))
        print('DELETE %s(%s) -> %d' % (nm, j['id'][:8], st), flush=True)

# 2) cloud_admin 单独重试看错误
import time
time.sleep(1)
st, raw = req('POST', '/projects/%s/jwks' % P,
              {'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs', 'provider_name': 'sec4-cadmin',
               'role_names': ['cloud_admin']})
print('POST cloud_admin -> %d | %s' % (st, raw[:400].decode(errors='replace')), flush=True)
time.sleep(1)
st, raw = req('POST', '/projects/%s/jwks' % P,
              {'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs', 'provider_name': 'sec4-neonsuper',
               'role_names': ['neon_superuser']})
print('POST neon_superuser -> %d | %s' % (st, raw[:400].decode(errors='replace')), flush=True)

# 3) PG 清理畸形角色
import psycopg
from psycopg import sql
try:
    conn = psycopg.connect('postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb', connect_timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE '%pwn%' OR rolname LIKE '%sec%' OR rolname LIKE '%NeonDb%' OR rolname LIKE '%\"%'")
    bad = [r[0] for r in cur.fetchall()]
    print('bad roles:', bad, flush=True)
    for name in bad:
        try:
            cur.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(name)))
            print('dropped:', name, flush=True)
        except Exception as e:
            print('drop fail', name, str(e)[:120], flush=True)
    conn.commit()
    conn.close()
except Exception as e:
    print('PG err:', e, flush=True)
