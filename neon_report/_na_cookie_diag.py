# -*- coding: utf-8 -*-
"""诊断:sign-in 响应 Set-Cookie 全量 + cookie 重放认证"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
ORIGIN = 'http://localhost:3000'
EMAIL = 'libobo1229+na1@gmail.com'
PASS = 'SecTest!2026pass'

def req(method, path, body=None, cookie=None, hdrs=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
             'Origin': ORIGIN}
        if cookie:
            h['Cookie'] = cookie
        if hdrs:
            h.update(hdrs)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status
        sc = r.headers.get_all('Set-Cookie') if r.headers else None
        conn.close()
        return st, raw[:400], sc
    except Exception as e:
        return 0, str(e).encode()[:150], None

st, raw, sc = req('POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PASS})
print('[signin] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)
if sc:
    for c in sc:
        print('  Set-Cookie:', c[:200], flush=True)
    time.sleep(0.5)

# 用完整 cookie 重放
if sc:
    ck = '; '.join(c.split(';')[0] for c in sc)
    print('using cookie:', ck[:150], flush=True)
    st2, raw2, _ = req('GET', '/neondb/auth/organization/list', cookie=ck)
    print('[list w/ cookie] -> %d | %s' % (st2, raw2.decode(errors='replace')[:300]), flush=True)
    time.sleep(0.5)
    st3, raw3, _ = req('POST', '/neondb/auth/organization/create', {'name': 'probe', 'slug': 'probe-x1'}, cookie=ck)
    print('[create w/ cookie] -> %d | %s' % (st3, raw3.decode(errors='replace')[:300]), flush=True)

# 备选 header 变体
st4, raw4, _ = req('GET', '/neondb/auth/organization/list', hdrs={'x-auth-token': 'pVua1lI9eu7atpZPuLQVZwTZ4UgvFa7N'})
print('[list x-auth-token] -> %d | %s' % (st4, raw4.decode(errors='replace')[:200]), flush=True)
