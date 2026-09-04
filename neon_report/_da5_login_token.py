# -*- coding: utf-8 -*-
"""Data API 面[4]:na2 登录 -> 用户 JWT(/token) -> payload 分析
+ neon_auth 表 owner/ACL(写权限归属)
零破坏:登录只读;PG 只读。"""
import http.client, ssl, json, base64, time, sys

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(host, method, path, body=None, hdr=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if hdr: h.update(hdr)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status
    sc = r.headers.get_all('Set-Cookie') if r.headers else None
    conn.close()
    return st, raw, sc

def b64u_dec(s):
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s)

# 1) 登录 na2
print('=== [1] sign-in na2 ===', flush=True)
st, raw, sc = req(NA, 'POST', '/neondb/auth/sign-in/email',
                  {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                  {'Origin': 'http://localhost:3000'})
print('status:', st)
body = raw.decode(errors='replace')
print('body head:', body[:300].replace('\n', ' '), flush=True)
cookies = {}
if sc:
    for c in sc:
        kv = c.split(';')[0]
        if '=' in kv:
            k, v = kv.split('=', 1)
            cookies[k.strip()] = v.strip()
            print('cookie:', k.strip())
print('cookies keys:', list(cookies.keys()), flush=True)

sess = None
try:
    d = json.loads(raw)
    sess = d.get('token') or (d.get('session') or {}).get('token')
except Exception:
    pass
if not sess and cookies:
    sess = cookies.get('better-auth.session_token') or cookies.get('neon_auth.session_token') or \
           next(iter(cookies.values()), None)
print('session token len:', len(sess or ''), flush=True)

# 2) 拿 JWT
print('\n=== [2] neonauth /token ===', flush=True)
hdr = {}
if sess:
    hdr['Authorization'] = 'Bearer ' + sess
# cookie 也带上
ck = '; '.join('%s=%s' % kv for kv in cookies.items()) if cookies else None
if ck:
    hdr['Cookie'] = ck
for path in ['/neondb/auth/token', '/neondb/auth/jwks']:
    st2, raw2, _ = req(NA, 'POST' if 'token' in path else 'GET', path, hdr=hdr)
    print('[%s] -> %d | %s' % (path, st2, raw2[:200].decode(errors='replace').replace('\n', ' ')), flush=True)
    if st2 == 200 and 'token' in path:
        try:
            tj = json.loads(raw2)
            tok = tj.get('token', '')
            parts = tok.split('.')
            if len(parts) == 3:
                print('  jwt header:', json.dumps(json.loads(b64u_dec(parts[0]))))
                print('  jwt payload:', json.dumps(json.loads(b64u_dec(parts[1])), ensure_ascii=False))
        except Exception as e:
            print('  parse err:', e, flush=True)
    time.sleep(0.5)

# 3) PG: neon_auth 表 owner/ACL
print('\n=== [3] neon_auth ACL ===', flush=True)
import psycopg
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""SELECT c.relname, pg_get_userbyid(c.relowner),
               array_to_string(c.relacl, ' | ') AS acl
               FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = 'neon_auth' AND c.relkind IN ('r','v')
               ORDER BY c.relname""")
for r in cur.fetchall():
    print('  %s owner=%s acl=%s' % (r[0], r[1], (r[2] or '')[:200]))
conn.close()
