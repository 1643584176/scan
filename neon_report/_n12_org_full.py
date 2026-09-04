# -*- coding: utf-8 -*-
"""Organization 邀请链完整验证(修正):
sign-up 新用户(未验证) -> na2 create org(slug) -> invite -> 未验证用户 list/accept"""
import http.client, ssl, json, time, base64

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
NEW_EMAIL = 'libobo1229+secn12@gmail.com'
NEW_PW = 'SecTest!2026pass2'

def req(method, path, body=None, cookie=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Origin': ORIGIN}
        if cookie:
            h['Cookie'] = cookie
        conn.request(method, '/neondb/auth' + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
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
        return st, raw.decode('utf-8', 'replace'), ck
    except Exception as e:
        return -1, 'EXC %s' % e, ''

def dec(s):
    s2 = s.replace('-', '+').replace('_', '/')
    s2 += '=' * (-len(s2) % 4)
    return base64.b64decode(s2).decode('utf-8', 'replace')

print('=== [1] sign-up 新用户 ===', flush=True)
st, raw, _ = req('POST', '/sign-up/email', {'email': NEW_EMAIL, 'password': NEW_PW, 'name': 'sec-n12'})
print('sign-up:', st, raw[:300].replace('\n', ' '), flush=True)
time.sleep(0.5)

print('\n=== [2] 新用户登录 + emailVerified ===', flush=True)
st, raw, ck_new = req('POST', '/sign-in/email', {'email': NEW_EMAIL, 'password': NEW_PW})
print('sign-in new:', st, raw[:150].replace('\n', ' '), 'ck:', ck_new[:40], flush=True)
if ck_new:
    st_t, raw_t, _ = req('GET', '/token', cookie=ck_new)
    if st_t == 200:
        p = json.loads(dec(json.loads(raw_t).get('token', '').split('.')[1]))
        print('  new user emailVerified=%s id=%s' % (p.get('emailVerified'), p.get('id')), flush=True)
        NEW_UID = p.get('id')
    # sign-out 清理会话(不破坏)
    req('POST', '/sign-out', {}, cookie=ck_new)

print('\n=== [3] na2 登录 + create org(slug) ===', flush=True)
st, raw, ck2 = req('POST', '/sign-in/email', {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'})
print('na2 sign-in:', st, flush=True)
org_id = None
if ck2:
    st, raw, _ = req('POST', '/organization/create', {'name': 'sec-n12-org', 'slug': 'sec-n12-org'}, cookie=ck2)
    print('create org:', st, raw[:300].replace('\n', ' '), flush=True)
    try:
        d = json.loads(raw)
        org_id = (d.get('data') or d).get('id')
        print('org_id:', org_id, flush=True)
    except Exception:
        pass

print('\n=== [4] na2 invite 新用户 ===', flush=True)
inv_id = None
if ck2 and org_id:
    st, raw, _ = req('POST', '/organization/invite-member',
                     {'email': NEW_EMAIL, 'role': 'member', 'organizationId': org_id}, cookie=ck2)
    print('invite:', st, raw[:400].replace('\n', ' '), flush=True)
    try:
        d = json.loads(raw)
        dd = d.get('data') or d
        inv_id = dd.get('id') if isinstance(dd, dict) else None
        print('invitation_id:', inv_id, flush=True)
    except Exception:
        pass

print('\n=== [5] 未验证用户接受链 ===', flush=True)
if inv_id:
    st, raw, ck_new2 = req('POST', '/sign-in/email', {'email': NEW_EMAIL, 'password': NEW_PW})
    print('new sign-in:', st, flush=True)
    if ck_new2:
        # listUserInvitations 变体
        for m, p, b in [('GET', '/organization/invitations', None),
                        ('POST', '/organization/invitations', {}),
                        ('GET', '/organization/invitation', None),
                        ('GET', '/organization/invitations/list', None),
                        ('POST', '/organization/list-invitations', {})]:
            st2, raw2, _ = req(m, p, b, cookie=ck_new2)
            print('[%s %s] -> %d %s' % (m, p, st2, raw2[:220].replace('\n', ' ')), flush=True)
            time.sleep(0.2)
        # by-ID 接受
        st3, raw3, _ = req('POST', '/organization/accept-invitation', {'invitationId': inv_id}, cookie=ck_new2)
        print('[accept-invitation %s] -> %d %s' % (inv_id, st3, raw3[:250].replace('\n', ' ')), flush=True)
        st4, raw4, _ = req('POST', '/organization/get-invitation', {'invitationId': inv_id}, cookie=ck_new2)
        print('[get-invitation] -> %d %s' % (st4, raw4[:250].replace('\n', ' ')), flush=True)
        # 接受后成员状态
        st5, raw5, _ = req('GET', '/organization/list', cookie=ck_new2)
        print('[new org list] -> %d %s' % (st5, raw5[:400].replace('\n', ' ')), flush=True)

print('\n=== [6] na2 收尾确认 ===', flush=True)
st6, raw6, _ = req('GET', '/organization/list', cookie=ck2)
print('na2 orgs:', st6, raw6[:600].replace('\n', ' '), flush=True)
