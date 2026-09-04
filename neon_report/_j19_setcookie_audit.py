# -*- coding: utf-8 -*-
"""Set-Cookie 属性一致性审计(Partitioned 是否所有重发都带?)
+ list-sessions 内容面 + sign-out 后 cookie 状态"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
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

def dump_sc(tag, hdrs):
    scs = hdrs.get_all('Set-Cookie') or []
    for sc in scs:
        props = []
        for part in sc.split(';')[1:]:
            p = part.strip().split('=')[0]
            if p:
                props.append(p)
        print('  [%s] Set-Cookie attrs: %s' % (tag, ', '.join(props) if props else '(无属性!)'))
    if not scs:
        print('  [%s] 无 Set-Cookie' % tag)

st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    origin='http://localhost:3000', raw_headers=True)
cook = '; '.join(c.split(';')[0] for c in hdrs.get_all('set-cookie'))
print('login=%d' % st)
dump_sc('sign-in', hdrs)

print('\n=== [1] 各端点 Set-Cookie 属性一致性 ===')
# update-user
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/update-user', {'name': 'sec-na-2'},
                    headers={'Cookie': cook}, origin='http://localhost:3000', raw_headers=True)
print('update-user -> %d' % st)
dump_sc('update-user', hdrs)
# change-password
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/change-password',
                    {'currentPassword': PWD, 'newPassword': PWD},
                    headers={'Cookie': cook}, origin='http://localhost:3000', raw_headers=True)
print('change-password -> %d' % st)
dump_sc('change-password', hdrs)
# GET /token(核心: 每次调用是否重发 cookie)
st, raw, hdrs = req(NA, 'GET', '/neondb/auth/token', headers={'Cookie': cook}, raw_headers=True)
print('GET /token -> %d' % st)
dump_sc('token', hdrs)
# GET /get-session
st, raw, hdrs = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': cook}, raw_headers=True)
print('get-session -> %d' % st)
dump_sc('get-session', hdrs)
# GET /list-sessions
st, raw, hdrs = req(NA, 'GET', '/neondb/auth/list-sessions', headers={'Cookie': cook}, raw_headers=True)
print('list-sessions -> %d' % st)
dump_sc('list-sessions', hdrs)
# revoke-sessions(注意: 传不存在的 token 看行为)
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/revoke-sessions', {'token': 'zz_no_such'},
                    headers={'Cookie': cook}, origin='http://localhost:3000', raw_headers=True)
print('revoke-sessions -> %d %s' % (st, raw.decode(errors='replace')[:60]))
dump_sc('revoke-sessions', hdrs)

print('\n=== [2] list-sessions 内容面(真cookie x evil origin) ===')
st, raw, hdrs = req(NA, 'GET', '/neondb/auth/list-sessions', headers={'Cookie': cook},
                    origin='https://evil.com', raw_headers=True)
print('evil -> %d  ACAO=%s creds=%s' % (st, hdrs.get('access-control-allow-origin'),
      hdrs.get('access-control-allow-credentials')))
print('  body=%s' % raw.decode(errors='replace')[:500])

print('\n=== [3] sign-out 的 Set-Cookie(清除是否也带属性) ===')
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-out', {}, headers={'Cookie': cook},
                    origin='http://localhost:3000', raw_headers=True)
print('sign-out -> %d' % st)
dump_sc('sign-out', hdrs)
