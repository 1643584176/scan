# -*- coding: utf-8 -*-
"""邀请绑定测试:注册 +na3 + 邀请幽灵邮箱 + 用 +na3 accept(校验 email 归属)"""
import http.client, ssl, json, time, uuid

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
s = json.load(open('_na_sess.json'))
ck1 = s['ck1']
ORG = 'cb082192-236a-482e-82d5-43a2c778facb'

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
            st = r.status
            sc = r.headers.get_all('Set-Cookie') if r.headers else None
            conn.close()
            return st, raw[:500], sc
        except Exception as e:
            return 0, str(e).encode()[:120], None
    return 0, b'', None

def show(tag, r, n=350):
    st, raw, sc = r
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:n]), flush=True)
    time.sleep(0.8)

# 1) 注册 +na3
st, raw, sc = req('POST', '/neondb/auth/sign-up/email', {
    'email': 'libobo1229+na3@gmail.com', 'password': 'SecTest!2026pass3', 'name': 'sec-na-3'})
show('signup na3', (st, raw, sc))
ck3 = None
if sc:
    ck3 = '; '.join(c.split(';')[0] for c in sc if 'session_token' in c)
print('ck3 set:', bool(ck3), flush=True)

# 2) na1 邀请幽灵邮箱(非 na3)
ghost = 'ghost-%s@nomail.invalid' % uuid.uuid4().hex[:6]
st, raw, sc = req('POST', '/neondb/auth/organization/invite-member',
                  {'organizationId': ORG, 'email': ghost, 'role': 'admin'}, cookie=ck1)
show('na1 invite ghost email', (st, raw, sc))
try:
    inv_id = json.loads(raw).get('invitation', {}).get('id') or json.loads(raw).get('id')
except Exception:
    inv_id = None
print('ghost inv_id:', inv_id, flush=True)

# 3) na3(不是被邀请邮箱)accept
if inv_id and ck3:
    st, raw, sc = req('POST', '/neondb/auth/organization/accept-invitation', {'invitationId': inv_id}, cookie=ck3)
    show('na3 accept ghost inv', (st, raw, sc))
    time.sleep(0.5)
    st, raw, sc = req('GET', '/neondb/auth/organization/list', cookie=ck3)
    show('na3 org list', (st, raw, sc))

# 4) 对照:na1 邀请 na3 真实邮箱,na3 accept(正常路径)
st, raw, sc = req('POST', '/neondb/auth/organization/invite-member',
                  {'organizationId': ORG, 'email': 'libobo1229+na3@gmail.com', 'role': 'member'}, cookie=ck1)
show('na1 invite na3 real', (st, raw, sc))
try:
    inv2 = json.loads(raw).get('invitation', {}).get('id') or json.loads(raw).get('id')
except Exception:
    inv2 = None
if inv2 and ck3:
    st, raw, sc = req('POST', '/neondb/auth/organization/accept-invitation', {'invitationId': inv2}, cookie=ck3)
    show('na3 accept real inv', (st, raw, sc))

print('DONE', flush=True)
