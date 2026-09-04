# -*- coding: utf-8 -*-
"""OAuth init token 链完整黑盒:
1. POST social(localhost) -> init token
2. GET init?token=X -> 302 Google? state/redirect_uri/scope 分析
3. state 解码(寻找 redirectTo/注入点)
4. 无效 token/重放/过期/参数覆盖
5. 无 cookie 场景行为"""
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

# 1. 发起 OAuth (redirectTo=localhost:3000 合法)
st, raw, hdrs = req('POST', '/neondb/auth/sign-in/social',
                    {'provider': 'google', 'redirectTo': 'http://localhost:3000/dash'},
                    {'Origin': 'http://localhost:3000'}, raw_headers=True)
print('[1] POST social -> %d %s' % (st, raw.decode(errors='replace')[:200]))
try:
    url = json.loads(raw).get('url')
except Exception:
    url = None
print('    init url:', url)

if url:
    init_path = urllib.parse.urlparse(url).path + '?' + urllib.parse.urlparse(url).query
    # 2. GET init (无 cookie)
    st, raw, hdrs = req('GET', init_path, raw_headers=True)
    loc = hdrs.get('location')
    print('\n[2] GET init 无cookie -> %d' % st)
    print('    Location: %s' % (loc or raw.decode(errors='replace')[:200]))
    if loc:
        u = urllib.parse.urlparse(loc)
        q = urllib.parse.parse_qs(u.query)
        print('    跳转域: %s' % u.netloc)
        print('    参数: %s' % json.dumps({k: v[0][:120] for k, v in q.items()}, ensure_ascii=False)[:600])
        state = q.get('state', [''])[0]
        redirect_uri = q.get('redirect_uri', [''])[0]
        client_id = q.get('client_id', [''])[0]
        print('    client_id: %s' % client_id[:80])
        print('    redirect_uri: %s' % redirect_uri[:200])
        # state 解码尝试
        for enc in ('utf-8', 'latin1'):
            try:
                dec = base64.urlsafe_b64decode(state + '==')
                print('    state(base64解码): %s' % dec.decode(enc, errors='replace')[:300])
                break
            except Exception:
                pass
        # 3. GET init 重放(第二次)
        st2, raw2, hdrs2 = req('GET', init_path, raw_headers=True)
        print('\n[3] init 重放 -> %d loc=%s' % (st2, (hdrs2.get('location') or '')[:100]))
        # 4. 参数覆盖尝试
        for extra in ('&redirectTo=https://evil.com', '&provider=github', '&state=AAAA'):
            st3, raw3, hdrs3 = req('GET', init_path + extra, raw_headers=True)
            l3 = hdrs3.get('location') or ''
            print('[4] init%s -> %d loc=%s' % (extra[:30], st3, l3[:100]))

# 5. 无效 token
for t in ('00000000-0000-0000-0000-000000000000', 'x', ''):
    st, raw, hdrs = req('GET', '/neondb/auth/sign-in/social/init?token=%s' % t, raw_headers=True)
    print('\n[5] init token=%r -> %d loc=%s body=%s' % (t, st, (hdrs.get('location') or '')[:80],
          raw.decode(errors='replace')[:100]))
    time.sleep(0.2)

# 6. POST 到 init 端点 + 变体路径
for p in ('/neondb/auth/sign-in/social/init', '/neondb/auth/sign-in/social/init?token=00000000-0000-0000-0000-000000000000',
          '/neondb/auth/sign-in/social/callback', '/neondb/auth/sign-in/google', '/neondb/auth/sign-in/github',
          '/neondb/auth/social/init'):
    st, raw, hdrs = req('GET', p, raw_headers=True)
    print('[6] GET %s -> %d %s' % (p[:55], st, (hdrs.get('location') or raw.decode(errors='replace')[:80])))
    time.sleep(0.2)
