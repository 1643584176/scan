# -*- coding: utf-8 -*-
"""跨站 JWT 读取链完整性验证 + console-stage CORS 反射面
A. get-session 内容面 / JWT 刷新语义(旧 JWT 是否仍有效)
B. console API ACAO 反射 + keycloak cookie 属性观察"""
import http.client, ssl, json, time, sys, os

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
CONSOLE = 'console-stage.neon.build'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'

def req(host, method, path, body=None, headers=None, origin=None, raw_headers=False):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if origin is not None:
        h['Origin'] = origin
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    data = r.read()
    st = r.status
    hdrs = r.headers
    conn.close()
    if raw_headers:
        return st, data, hdrs
    return st, data

# 登录 auth
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    origin='http://localhost:3000', raw_headers=True)
cook = '; '.join(c.split(';')[0] for c in hdrs.get_all('set-cookie'))
print('login=%d' % st)

print('\n=== [A1] get-session 内容面(真cookie x evil/good origin) ===')
for o in ('https://evil.com', 'http://localhost:3000', None):
    st, raw, hdrs = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': cook},
                        origin=o, raw_headers=True)
    print('  origin=%s -> %d  ACAO=%s creds=%s\n    body=%s' % (
        o, st, hdrs.get('access-control-allow-origin'),
        hdrs.get('access-control-allow-credentials'), raw.decode(errors='replace')[:300]))
    time.sleep(0.3)

print('\n=== [A2] JWT 刷新语义: 两次 GET /token + 旧 JWT 在 Data API 有效性 ===')
j1 = json.loads(req(NA, 'GET', '/neondb/auth/token', headers={'Cookie': cook})[1]).get('token')
time.sleep(1)
j2 = json.loads(req(NA, 'GET', '/neondb/auth/token', headers={'Cookie': cook})[1]).get('token')
print('  jwt1 != jwt2:', j1 != j2)
# 解码 exp
import base64
def b64d(s):
    return json.loads(base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)))
p1, p2 = b64d(j1.split('.')[1]), b64d(j2.split('.')[1])
print('  jwt1 exp-iat=%d  jwt2 exp-iat=%d' % (p1['exp'] - p1['iat'], p2['exp'] - p2['iat']))
# 旧 JWT 调 Data API
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
for tag, j in (('jwt1(旧)', j1), ('jwt2(新)', j2)):
    st, raw = req(DA_HOST, 'GET', '/neondb/rest/v1/?limit=1', headers={'Authorization': 'Bearer ' + j})
    print('  DataAPI %s -> %d %s' % (tag, st, raw.decode(errors='replace')[:80]))
    time.sleep(0.3)

print('\n=== [A3] sign-in/email x evil origin(登录端点校验对照) ===')
st, raw = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
              origin='https://evil.com')
print('  sign-in evil-origin -> %d %s' % (st, raw.decode(errors='replace')[:80]))

print('\n=== [B1] console API x evil Origin ACAO 反射 ===')
from _neon_creds_stage import cookie_str
for p in ('/api/v2/projects', '/api/v2/users/me'):
    st, raw, hdrs = req(CONSOLE, 'GET', p, headers={'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'},
                        origin='https://evil.com', raw_headers=True)
    print('  GET %s evil -> %d  ACAO=%s creds=%s body=%s' % (
        p, st, hdrs.get('access-control-allow-origin'),
        hdrs.get('access-control-allow-credentials'), raw.decode(errors='replace')[:120]))
    time.sleep(0.3)
st, raw, hdrs = req(CONSOLE, 'GET', '/api/v2/projects', headers={'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'},
                    origin=None, raw_headers=True)
print('  GET /api/v2/projects no-origin -> %d  ACAO=%s' % (st, hdrs.get('access-control-allow-origin')))
# OPTIONS 预检
st, raw, hdrs = req(CONSOLE, 'OPTIONS', '/api/v2/projects', headers={'Origin': 'https://evil.com',
                    'Access-Control-Request-Method': 'GET'}, raw_headers=True)
print('  OPTIONS evil -> %d  ACAO=%s creds=%s' % (st, hdrs.get('access-control-allow-origin'),
      hdrs.get('access-control-allow-credentials')))
# POST 对照(应被 CSRF 挡——确认 console 有独立防护层)
st, raw, hdrs = req(CONSOLE, 'POST', '/api/v2/projects', {'name': 'k-csrftest', 'region_id': 'aws-us-east-2'},
                    headers={'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'}, origin='https://evil.com', raw_headers=True)
print('  POST /api/v2/projects evil(无csrf头) -> %d  ACAO=%s body=%s' % (
    st, hdrs.get('access-control-allow-origin'), raw.decode(errors='replace')[:100]))

print('\n=== [B2] keycloak 端点 CORS ===')
for p in ('/realms/staging-realm/.well-known/openid-configuration',
          '/realms/staging-realm/protocol/openid-connect/auth'):
    st, raw, hdrs = req(CONSOLE, 'GET', p, origin='https://evil.com', raw_headers=True)
    print('  GET %s -> %d  ACAO=%s' % (p.split('?')[0][:60], st, hdrs.get('access-control-allow-origin')))
