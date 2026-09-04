# -*- coding: utf-8 -*-
"""Neon Auth org 双用户越权矩阵(cookie 认证,带速率控制)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'

def signin(email, password):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Origin': ORIGIN}
    conn.request('POST', '/neondb/auth/sign-in/email', body=json.dumps({'email': email, 'password': password}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    sc = r.headers.get_all('Set-Cookie') if r.headers else None
    st = r.status; conn.close()
    if st == 200 and sc:
        ck = '; '.join(c.split(';')[0] for c in sc if 'session_token' in c)
        return json.loads(raw)['user']['id'], ck
    return None, None

def req(method, path, body=None, cookie=None, origin=ORIGIN):
    for _ in range(2):
        try:
            conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
            if origin:
                h['Origin'] = origin
            if cookie:
                h['Cookie'] = cookie
            conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = conn.getresponse(); raw = r.read()
            st = r.status; conn.close()
            return st, raw[:500]
        except Exception as e:
            return 0, str(e).encode()[:120]
    return 0, b''

def show(tag, st, raw, n=400):
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:n]), flush=True)
    time.sleep(0.7)

# 0) 双用户登录
uid1, ck1 = signin('libobo1229+na1@gmail.com', 'SecTest!2026pass')
uid2, ck2 = signin('libobo1229+na2@gmail.com', 'SecTest!2026pass2')
print('na1 uid:', uid1, '| na2 uid:', uid2, flush=True)
if not ck1 or not ck2:
    print('FATAL login'); raise SystemExit
json.dump({'ck1': ck1, 'ck2': ck2, 'uid1': uid1, 'uid2': uid2}, open('_na_sess.json', 'w'))

ORG = 'cb082192-236a-482e-82d5-43a2c778facb'  # probe-x1 (na1 owner)

# 1) 基线:双方 org list
st, raw = req('GET', '/neondb/auth/organization/list', cookie=ck1)
show('na1 org list', st, raw)
st, raw = req('GET', '/neondb/auth/organization/list', cookie=ck2)
show('na2 org list', st, raw)

# 2) na2 未接受邀请前直接变异:na2 调 org 管理端点(非成员)
st, raw = req('POST', '/neondb/auth/organization/update', {'organizationId': ORG, 'data': {'name': 'pwned'}}, cookie=ck2)
show('na2(non-member) update org', st, raw)
st, raw = req('POST', '/neondb/auth/organization/delete', {'organizationId': ORG}, cookie=ck2)
show('na2(non-member) delete org', st, raw)
st, raw = req('POST', '/neondb/auth/organization/leave', {'organizationId': ORG}, cookie=ck2)
show('na2(non-member) leave org', st, raw)

# 3) na1 invite na2 as member(role=member)
st, raw = req('POST', '/neondb/auth/organization/invite-member',
              {'organizationId': ORG, 'email': 'libobo1229+na2@gmail.com', 'role': 'member'}, cookie=ck1)
show('na1 invite na2 member', st, raw)
try:
    inv_id = json.loads(raw).get('invitation', {}).get('id') or json.loads(raw).get('id')
except Exception:
    inv_id = None
print('inv_id:', inv_id, flush=True)

# 4) na2 accept 后立即变异测试
st, raw = req('POST', '/neondb/auth/organization/accept-invitation', {'invitationId': inv_id}, cookie=ck2)
show('na2 accept', st, raw)
time.sleep(0.5)
st, raw = req('GET', '/neondb/auth/organization/list', cookie=ck2)
show('na2 org list (accepted)', st, raw)

# 5) 越权矩阵:na2(member 角色)
st, raw = req('POST', '/neondb/auth/organization/update-member-role',
              {'organizationId': ORG, 'memberId': uid2, 'role': 'owner'}, cookie=ck2)
show('na2 self-promote owner', st, raw)
st, raw = req('POST', '/neondb/auth/organization/invite-member',
              {'organizationId': ORG, 'email': 'x@x.com', 'role': 'admin'}, cookie=ck2)
show('na2 invite as admin', st, raw)
st, raw = req('POST', '/neondb/auth/organization/update', {'organizationId': ORG, 'data': {'name': 'pwned-by-member'}}, cookie=ck2)
show('na2 update org', st, raw)
st, raw = req('POST', '/neondb/auth/organization/remove-member', {'organizationId': ORG, 'memberIdOrEmail': uid1}, cookie=ck2)
show('na2 remove owner', st, raw)

# 6) owner 侧对照:na1 把 na2 降级/移除
st, raw = req('POST', '/neondb/auth/organization/update-member-role',
              {'organizationId': ORG, 'memberId': uid2, 'role': 'member'}, cookie=ck1)
show('na1 set na2 member', st, raw)
st, raw = req('POST', '/neondb/auth/organization/remove-member', {'organizationId': ORG, 'memberIdOrEmail': uid2}, cookie=ck1)
show('na1 remove na2', st, raw)

print('DONE', flush=True)
