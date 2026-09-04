# -*- coding: utf-8 -*-
"""跨 org 隔离 + members 端点 + slug 冲突 + 邀请撤销"""
import http.client, ssl, json, time, uuid

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
s = json.load(open('_na_sess.json'))
ck1, ck3 = s['ck1'], None
ORG1 = 'cb082192-236a-482e-82d5-43a2c778facb'

# na3 重新登录(注册 token 可能已过期/或有效;直接 sign-in 稳妥)
def signin(email, password):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Origin': ORIGIN}
    conn.request('POST', '/neondb/auth/sign-in/email', body=json.dumps({'email': email, 'password': password}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    sc = r.headers.get_all('Set-Cookie') if r.headers else None
    st = r.status; conn.close()
    if st == 200 and sc:
        return '; '.join(c.split(';')[0] for c in sc if 'session_token' in c)
    return None

ck3 = signin('libobo1229+na3@gmail.com', 'SecTest!2026pass3')
print('ck3 ok:', bool(ck3), flush=True)

def req(method, path, body=None, cookie=None, origin=ORIGIN):
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
        return st, raw[:450]
    except Exception as e:
        return 0, str(e).encode()[:120]

def show(tag, r, n=300):
    st, raw = r
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:n]), flush=True)
    time.sleep(0.8)

# 1) na1 建 org2
slug2 = 'sec-org2-' + uuid.uuid4().hex[:8]
st, raw = req('POST', '/neondb/auth/organization/create', {'name': 'org2', 'slug': slug2}, cookie=ck1)
show('na1 create org2', (st, raw))
try:
    org2 = json.loads(raw).get('organization', {}).get('id') or json.loads(raw).get('id')
except Exception:
    org2 = None
print('org2:', org2, flush=True)

# 2) na3(org1 member)跨 org 操作 org2
if org2:
    show('na3 cross-org update org2', req('POST', '/neondb/auth/organization/update',
        {'organizationId': org2, 'data': {'name': 'pwned'}}, cookie=ck3))
    show('na3 cross-org invite', req('POST', '/neondb/auth/organization/invite-member',
        {'organizationId': org2, 'email': 'x@x.com', 'role': 'admin'}, cookie=ck3))
    show('na3 cross-org delete', req('POST', '/neondb/auth/organization/delete',
        {'organizationId': org2}, cookie=ck3))
    show('na3 cross-org members', req('GET', '/neondb/auth/organization/members?organizationId=' + org2, cookie=ck3))

# 3) na1 正常查 org2 members(对照)
show('na1 org2 members GET', req('GET', '/neondb/auth/organization/members?organizationId=' + org2, cookie=ck1))
show('na1 org1 members GET', req('GET', '/neondb/auth/organization/members?organizationId=' + ORG1, cookie=ck1))

# 4) slug 冲突:na2 用 org2 同 slug 建 org
st, raw = req('POST', '/neondb/auth/organization/create', {'name': 'dup', 'slug': slug2}, cookie=ck3)
show('na3 create dup slug', (st, raw))

# 5) 撤销 ghost 邀请 + org2 清理
show('na1 cancel ghost inv', req('POST', '/neondb/auth/organization/cancel-invitation',
    {'invitationId': 'f70f70f1-426e-4ac5-bce7-3622c4816d48'}, cookie=ck1))
if org2:
    show('na1 delete org2', req('POST', '/neondb/auth/organization/delete', {'organizationId': org2}, cookie=ck1))

print('DONE', flush=True)
