# -*- coding: utf-8 -*-
"""读 jwks privateKey + sign-up 注册测试用户"""
import psycopg, http.client, ssl, json, time
ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'

# A) 读私钥
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('SELECT id, "publicKey", "privateKey", "expiresAt" FROM neon_auth.jwks')
rows = cur.fetchall()
print('jwks rows:', len(rows), flush=True)
for r in rows:
    print(' id:', r[0], flush=True)
    print(' pub:', str(r[1])[:100], flush=True)
    print(' priv:', str(r[2])[:120], flush=True)
    print(' exp:', r[3], flush=True)
    if r[2]:
        open(r'D:\scan\neon_report\_neonauth_priv.txt', 'w').write(str(r[2]))
        print('saved privateKey', flush=True)
conn.close()

# B) sign-up(带 Origin)
def na_req(method, path, body=None, hdrs=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
             'Origin': 'https://console-stage.neon.build'}
        if hdrs: h.update(hdrs)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status
        sc = r.headers.get_all('Set-Cookie') if r.headers else None
        conn.close()
        return st, raw[:500], sc
    except Exception as e:
        return 0, str(e).encode()[:200], None

st, raw, sc = na_req('POST', '/neondb/auth/sign-up/email',
                     {'email': 'libobo1229+na1@gmail.com', 'password': 'SecTest!2026pass', 'name': 'sec-na-1'})
print('\n[sign-up] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)
if sc: print('  cookies:', sc, flush=True)

time.sleep(1)
st, raw, sc = na_req('GET', '/neondb/auth/get-session')
print('[get-session] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)
if sc: print('  cookies:', sc, flush=True)
