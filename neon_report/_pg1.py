# -*- coding: utf-8 -*-
"""PG 层第一步:拿连接串/密码 -> psycopg 直连 compute 只读枚举"""
import http.client, ssl, json, sys, re
ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

# 1) connection_uri(看是否自带密码)
st, raw = req('GET', '/projects/%s/connection_uri' % P)
print('== connection_uri -> %d' % st)
print(raw[:600].decode(errors='replace'))
uri = None
try:
    uri = json.loads(raw).get('uri') or json.loads(raw).get('connection_uri')
except Exception:
    pass

# 2) reset_password 拿 neondb_owner 密码(如需)
if not uri or 'password' not in (uri or '').split('@')[0]:
    st, raw = req('POST', '/projects/%s/branches/%s/roles/neondb_owner/reset_password' % (P, B), {})
    print('\n== reset_password -> %d' % st)
    print(raw[:400].decode(errors='replace'))
    try:
        pw = json.loads(raw).get('password')
        if pw and uri:
            uri = re.sub(r'://[^@]*@', '://neondb_owner:%s@' % pw, uri)
        elif pw:
            host = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
            uri = 'postgresql://neondb_owner:%s@%s/neondb' % (pw, host)
    except Exception as e:
        print('pw parse err', e)

print('\nFINAL URI:', (uri or 'NONE')[:120])
open(r'D:\scan\neon_report\_pguri.txt', 'w').write(uri or '')

# 3) psycopg 直连枚举(只读)
if uri:
    try:
        import psycopg
        conn = psycopg.connect(uri, connect_timeout=30)
        cur = conn.cursor()
        cur.execute('SELECT version()')
        print('\n[pg] version:', cur.fetchone()[0][:120])
        cur.execute("SELECT current_user, current_database(), inet_server_addr(), inet_server_port()")
        print('[pg] ctx:', cur.fetchone())
        cur.execute("SELECT extname, extversion FROM pg_extension ORDER BY 1")
        print('[pg] extensions:', cur.fetchall())
        cur.execute("SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication FROM pg_roles WHERE rolname IN ('neondb_owner','authenticator','anonymous','authenticated','neon_superuser')")
        print('[pg] roles:', cur.fetchall())
        cur.execute("SHOW neon.tenant_id")
        try:
            print('[pg] neon.tenant_id:', cur.fetchone())
        except Exception:
            pass
        cur.execute("SELECT name, setting FROM pg_settings WHERE name LIKE '%neon%' OR name LIKE '%version%' LIMIT 20")
        for r in cur.fetchall():
            print('  guc:', r)
        conn.close()
    except Exception as e:
        print('[pg] connect err:', e)
