# -*- coding: utf-8 -*-
"""Data API JWT 面:登录拿真 token + JWKS 探测 + 真 token 访问基线"""
import http.client, ssl, json, time, base64

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'

def na_req(method, path, body=None, token=None, origin='http://localhost:3000', full=False):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if origin:
        h['Origin'] = origin
    if token:
        h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    cookies = r.headers.get_all('Set-Cookie') if r.headers else None
    conn.close()
    if full:
        return st, raw, cookies
    return st, raw[:400], cookies

def da_req(method, path, body=None, token=None):
    conn = http.client.HTTPSConnection(DA_HOST, timeout=20)
    h = {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Bug-Bounty': 'xxbo'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    st = r.status
    conn.close()
    return st, data

print('=== [1] JWKS 探测 ===')
for p in ('/.well-known/jwks.json', '/neondb/auth/.well-known/jwks.json', '/.well-known/openid-configuration'):
    st, raw, _ = na_req('GET', p)
    print('  %s -> %d | %s' % (p, st, raw.decode(errors='replace')[:400]))

print('\n=== [2] 登录拿 token(已有用户 +na2 / 主用户) ===')
for email, pwd in [('libobo1229+na2@gmail.com', 'SecTest!2026pass2'), ('libobo1229@gmail.com', None)]:
    if pwd is None:
        continue
    st, raw, cookies = na_req('POST', '/neondb/auth/sign-in/email', {'email': email, 'password': pwd, 'rememberMe': True}, full=True)
    print('  sign-in %s -> %d' % (email, st))
    print('    body: %s' % raw.decode(errors='replace')[:400])
    if cookies:
        for c in cookies:
            if 'token' in c.lower() or 'jwt' in c.lower() or 'session' in c.lower():
                print('    cookie[%s]: %s' % (c.split('=')[0], c[:120]))
    # 解析 body 里的 token
    try:
        j = json.loads(raw)
        tok = None
        if isinstance(j, dict):
            tok = j.get('token') or (j.get('data') or {}).get('token') if isinstance(j.get('data'), dict) else None
        if tok:
            print('    body token found: %s...' % tok[:80])
            parts = tok.split('.')
            if len(parts) >= 2:
                pad = lambda s: s + '=' * (-len(s) % 4)
                print('    header: %s' % base64.urlsafe_b64decode(pad(parts[0])).decode('utf-8', 'ignore'))
                print('    payload: %s' % base64.urlsafe_b64decode(pad(parts[1])).decode('utf-8', 'ignore'))
    except Exception as e:
        print('    parse err:', e)

print('\n=== [3] 尝试 cookie session 换 JWT(Better Auth get-session) ===')
st, raw, _ = na_req('GET', '/neondb/auth/get-session')
print('  get-session(no cookie) -> %d %s' % (st, raw.decode(errors='replace')[:200]))
