# -*- coding: utf-8 -*-
"""注册 +na2 用户 + 基础端点面枚举(只读探测)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def na_req(method, path, body=None, token=None, origin='http://localhost:3000'):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if origin:
            h['Origin'] = origin
        if token:
            h['Authorization'] = 'Bearer ' + token
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status
        sc = r.headers.get_all('Set-Cookie') if r.headers else None
        conn.close()
        return st, raw[:300], sc
    except Exception as e:
        return 0, str(e).encode()[:150], None

# 注册 +na2
st, raw, sc = na_req('POST', '/neondb/auth/sign-up/email',
                     {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2', 'name': 'sec-na-2'})
print('[signup na2] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)
time.sleep(1)

# 端点探测(全部 GET,无副作用)
paths = [
    '/neondb/auth/get-session', '/neondb/auth/list-sessions', '/neondb/auth/organization/list',
    '/neondb/auth/admin/list-users', '/neondb/auth/admin/impersonate-user', '/neondb/auth/organization/members',
    '/neondb/auth/mfa/verify', '/neondb/auth/two-factor/verify', '/neondb/auth/webauthn/list',
]
for p in paths:
    st, raw, sc = na_req('GET', p)
    print('[%s] -> %d | %s' % (p, st, raw.decode(errors='replace')[:120]), flush=True)
    time.sleep(0.5)
