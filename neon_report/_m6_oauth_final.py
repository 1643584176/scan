# -*- coding: utf-8 -*-
"""OAuth 收尾: /token 端点用途 + callback 伪造 code 处理顺序 + state 过期
(判断网关对 code/state 的校验顺序与绑定)"""
import http.client, ssl, json, time, base64, urllib.parse

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(method, path, body=None, headers=None, raw_headers=False):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
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

print('=== [1] /neondb/auth/token 端点用途探测 ===')
bodies = [
    {'grant_type': 'authorization_code', 'code': 'x', 'redirect_uri': 'https://neonauth.us-east-2.aws.neon.build/auth/oauth/callback/google'},
    {'grant_type': 'refresh_token', 'refresh_token': 'x'},
    {'token': 'x'},
    {'client_id': 'x', 'client_secret': 'x', 'grant_type': 'client_credentials'},
]
for b in bodies:
    st, raw = req('POST', '/neondb/auth/token', b)
    print('POST /token %s -> %d %s' % (json.dumps(b)[:80], st, raw.decode(errors='replace')[:150]))
    time.sleep(0.3)

print('\n=== [2] callback 伪造 code + 真 state(校验顺序判定) ===')
# 拿一个真 state
st, raw = req('POST', '/neondb/auth/sign-in/social',
              {'provider': 'google', 'redirectTo': 'http://localhost:3000/dash'},
              {'Origin': 'http://localhost:3000'})
url = json.loads(raw).get('url', '')
t0 = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('token', [''])[0]
st, raw, hdrs = req('GET', '/neondb/auth/sign-in/social/init?token=' + t0, raw_headers=True)
loc = hdrs.get('location') or ''
state = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query).get('state', [''])[0]
print('真 state 前60:', state[:60])

print('\n--- 伪造 code + 真 state ---')
for code in ('fakecode123', 'x', ''):
    st, raw, hdrs = req('GET', '/neondb/auth/oauth/callback/google?code=%s&state=%s' % (code, urllib.parse.quote(state)),
                        raw_headers=True)
    l = hdrs.get('location') or ''
    print('[code=%r] -> %d loc=%s body=%s' % (code, st, l[:160], raw.decode(errors='replace')[:80]))
    time.sleep(0.3)

print('\n--- state 变体(签名破坏/缺失/他人) ---')
for s2 in ('AAAA', urllib.parse.quote('{"endpointId":"ep-crimson-fog-w2gucld1","database":"neondb","providerName":"google","timestamp":1}'),
           urllib.parse.quote('{"endpointId":"other-ep","database":"neondb","providerName":"google","timestamp":1788497949884}')):
    st, raw, hdrs = req('GET', '/neondb/auth/oauth/callback/google?code=fake&state=' + s2, raw_headers=True)
    l = hdrs.get('location') or ''
    print('[state=%s...] -> %d loc=%s' % (s2[:40], st, l[:160]))
    time.sleep(0.3)

print('\n=== [3] init token 过期行为(延时观察) ===')
# 无效 uuid 格式以外的 uuid token 已被测(VERIFICATION_NOT_FOUND); 这里只看重复 POST 是否每次都新 token
for i in range(2):
    st, raw = req('POST', '/neondb/auth/sign-in/social',
                  {'provider': 'google', 'redirectTo': 'http://localhost:3000/dash'},
                  {'Origin': 'http://localhost:3000'})
    print('POST social %d -> %s' % (i, raw.decode(errors='replace')[:120]))
    time.sleep(0.3)

print('\n=== [4] 共享网关直接路径探测(父域 neonauth) ===')
for p in ('/auth/oauth/callback/google', '/auth/oauth/callback/github', '/auth/oauth/callback',
          '/auth/oauth/authorize', '/auth/oauth/token', '/auth/jwks', '/auth/.well-known/jwks.json'):
    try:
        conn = http.client.HTTPSConnection('neonauth.us-east-2.aws.neon.build', context=ctx, timeout=15)
        conn.request('GET', p, headers={'User-Agent': 'Mozilla/5.0'})
        r = conn.getresponse()
        raw = r.read()
        print('[%s] -> %d %s' % (p, r.status, (r.getheader('location') or raw.decode(errors='replace')[:100])))
        conn.close()
    except Exception as e:
        print('[%s] EXC %s' % (p, e))
    time.sleep(0.3)
