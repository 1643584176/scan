# -*- coding: utf-8 -*-
"""B 建表授权 + A(orange-sun) JWT 打 B(sweet-hat) Data API"""
import http.client, ssl, json, time, os, sys, re, psycopg

ctx = ssl.create_default_context()
B_PG_HOST = 'ep-sweet-hat-w2w8qvav.us-east-2.aws.neon.build'
B_PWD = 'npg_zTFnHWDZyQ71'
B_DA = 'https://ep-sweet-hat-w2w8qvav.apirest.us-east-2.aws.neon.build/neondb/rest/v1'
B_NA = 'ep-sweet-hat-w2w8qvav.neonauth.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

# 1. B PG 建表
print('=== [1] B PG ===')
dbc = psycopg.connect('postgresql://neondb_owner:%s@%s/neondb' % (B_PWD, B_PG_HOST), connect_timeout=20)
dbc.autocommit = True
cur = dbc.cursor()
def q(sql):
    try:
        cur.execute(sql)
        try:
            return str(cur.fetchall())[:300]
        except Exception:
            return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]
print('  roles:', q("SELECT rolname FROM pg_roles WHERE rolname IN ('authenticated','anonymous','authenticator','neondb_owner')"))
print('  drop:', q('DROP TABLE IF EXISTS public.k_xprobe'))
print('  create:', q('CREATE TABLE public.k_xprobe (id serial PRIMARY KEY, secret text)'))
print('  insert:', q("INSERT INTO public.k_xprobe (secret) VALUES ('B-secret-1'), ('B-secret-2')"))
print('  grant:', q("GRANT SELECT, INSERT, UPDATE, DELETE ON public.k_xprobe TO authenticated"))
print('  grant seq:', q("GRANT USAGE ON SEQUENCE public.k_xprobe_id_seq TO authenticated"))
print('  view: SELECT has_table_privilege:',
      q("SELECT has_table_privilege('authenticated', 'public.k_xprobe', 'SELECT')"))
dbc.close()

# 2. B 的 JWKS vs A 的 JWKS
print('\n=== [2] JWKS 对比 ===')
st, raw = req(B_NA, 'GET', '/neondb/auth/.well-known/jwks.json')
print('  B jwks -> %d %s' % (st, raw.decode(errors='replace')[:250]))
st, raw = req('ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build', 'GET', '/neondb/auth/.well-known/jwks.json')
print('  A jwks -> %d %s' % (st, raw.decode(errors='replace')[:250]))

# 3. A 的 JWT
print('\n=== [3] A 登录拿 JWT ===')
conn = http.client.HTTPSConnection('ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build', context=ctx, timeout=20)
conn.request('POST', '/neondb/auth/sign-in/email',
             body=json.dumps({'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'}).encode(),
             headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'})
r = conn.getresponse(); r.read()
cks = r.headers.get_all('Set-Cookie')
conn.close()
cook = '; '.join(c.split(';')[0] for c in cks)
st, raw = req('ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build', 'GET', '/neondb/auth/token',
              headers={'Cookie': cook})
jwt_a = json.loads(raw).get('token', '')
print('  A jwt len=%d' % len(jwt_a))
import base64
def b64d(s):
    return json.loads(base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)))
ph = b64d(jwt_a.split('.')[0])
pl = b64d(jwt_a.split('.')[1])
print('  A header kid=%s alg=%s' % (ph.get('kid'), ph.get('alg')))
print('  A claims iss=%s aud=%s role=%s' % (pl.get('iss'), pl.get('aud'), pl.get('role')))

# 4. A JWT -> B Data API
print('\n=== [4] 核心: A JWT 打 B Data API ===')
m = re.match(r'https://([^/]+)(/.*)$', B_DA)
b_host, b_base = m.group(1), m.group(2).rstrip('/')
for tag, j in (('A-JWT(跨项目)', jwt_a), ('无JWT', None), ('假JWT', 'x.y.z')):
    hdrs = {'Authorization': 'Bearer ' + j} if j else None
    st, raw = req(b_host, 'GET', b_base + '/k_xprobe?select=id,secret&limit=5', headers=hdrs)
    print('  [%s] -> %d %s' % (tag, st, raw.decode(errors='replace')[:200]))
    time.sleep(0.5)

# 5. B 注册用户拿 B JWT(对照组)
print('\n=== [5] B 注册+登录(对照) ===')
B_MAIL = 'libobo1229+nb1@gmail.com'
st, raw = req(B_NA, 'POST', '/neondb/auth/sign-up/email',
              {'email': B_MAIL, 'password': 'SecTest!2026pass2', 'name': 'nb1'},
              {'Origin': 'http://localhost:3000'})
print('  B sign-up -> %d %s' % (st, raw.decode(errors='replace')[:150]))
st, raw = req(B_NA, 'POST', '/neondb/auth/sign-in/email',
              {'email': B_MAIL, 'password': 'SecTest!2026pass2'},
              {'Origin': 'http://localhost:3000'})
print('  B sign-in -> %d' % st)
# 需要 Set-Cookie —— req 不返回 headers, 重写登录
conn = http.client.HTTPSConnection(B_NA, context=ctx, timeout=20)
conn.request('POST', '/neondb/auth/sign-in/email',
             body=json.dumps({'email': B_MAIL, 'password': 'SecTest!2026pass2'}).encode(),
             headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'})
r = conn.getresponse(); r.read()
cks = r.headers.get_all('Set-Cookie')
conn.close()
cook_b = '; '.join(c.split(';')[0] for c in cks)
st, raw = req(B_NA, 'GET', '/neondb/auth/token', headers={'Cookie': cook_b})
jwt_b = json.loads(raw).get('token', '')
plb = b64d(jwt_b.split('.')[1])
print('  B jwt kid=%s role=%s iss=%s' % (b64d(jwt_b.split('.')[0]).get('kid'), plb.get('role'), plb.get('iss')))
st, raw = req(b_host, 'GET', b_base + '/k_xprobe?select=id,secret&limit=5',
              headers={'Authorization': 'Bearer ' + jwt_b})
print('  [B-JWT(同项目对照)] -> %d %s' % (st, raw.decode(errors='replace')[:200]))

# 6. 反向: B JWT 打 A Data API
print('\n=== [6] 反向: B JWT 打 A Data API ===')
st, raw = req('ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build',
              'GET', '/neondb/rest/v1/k_xprobe?select=id,secret&limit=5',
              headers={'Authorization': 'Bearer ' + jwt_b})
print('  [B-JWT -> A DataAPI] -> %d %s' % (st, raw.decode(errors='replace')[:200]))
