# -*- coding: utf-8 -*-
"""重建 org 闭环 member 自提权:
1. create org 完整响应(找 member id 字段)
2. invite+accept secn12 完整响应(找 member id)
3. ★ member 用自己 memberId 提权 owner/admin
4. 清理:删 org"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
PW = 'SecTest!2026pass2'
N12_EMAIL = 'libobo1229+secn12@gmail.com'

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

def req(cookie, method, path, body=None, raw_hdrs=False):
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

print('=== [1] create org 完整响应 ===', flush=True)
st, raw = req(ck2, 'POST', '/organization/create', {'name': 'sec-o6-org', 'slug': 'sec-o6-org'})
print('-> %d %s' % (st, raw[:800].replace('\n', ' ')), flush=True)
d = json.loads(raw)
org_id = d.get('id')
print('org_id:', org_id, flush=True)
# members 数组完整
members = d.get('members') or []
print('members count:', len(members), flush=True)
for m in members:
    print('  member obj:', json.dumps(m), flush=True)

print('\n=== [2] invite + accept 完整响应 ===', flush=True)
st, raw = req(ck2, 'POST', '/organization/invite-member',
              {'email': N12_EMAIL, 'role': 'member', 'organizationId': org_id})
print('invite -> %d %s' % (st, raw[:500].replace('\n', ' ')), flush=True)
inv_id = json.loads(raw).get('id')
st, raw = req(ck12, 'POST', '/organization/accept-invitation', {'invitationId': inv_id})
print('accept -> %d %s' % (st, raw[:600].replace('\n', ' ')), flush=True)
try:
    acc = json.loads(raw)
    print('accept keys:', list(acc.keys()), flush=True)
    for k, v in acc.items():
        if isinstance(v, dict):
            print('  %s: %s' % (k, json.dumps(v)[:400]), flush=True)
except Exception:
    pass

print('\n=== [3] member id 获取尝试 ===', flush=True)
# secn12 org list 全响应
st, raw = req(ck12, 'GET', '/organization/list')
print('member org list -> %d %s' % (st, raw[:800].replace('\n', ' ')), flush=True)
# owner org list 全响应
st, raw = req(ck2, 'GET', '/organization/list')
print('owner org list -> %d %s' % (st, raw[:800].replace('\n', ' ')), flush=True)

print('\n=== [4] 清理:owner delete org ===', flush=True)
st, raw = req(ck2, 'POST', '/organization/delete', {'organizationId': org_id})
print('delete -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
