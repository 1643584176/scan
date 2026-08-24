import io, json, urllib.request, urllib.error

def call(url, method='GET', body=None, headers=None, timeout=20):
    req = urllib.request.Request(url, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, dict(r.headers), r.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors='replace')
    except Exception as e:
        return -1, {}, str(e)

AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'

def base(cookie=AC, uid=A_UID):
    return {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}

# 1. create + grant
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base())
meta = json.loads(b)['meta']
aid = meta['id']
print('1. create:', aid, 'grantor_session_id=', meta['grantor_session_id'])
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(), 'X-Figma-User-ID': A_UID})
g = json.loads(b)['meta']['g_secret']
print('2. grant OK, g=', g)
print()

# 2. redeem 带 grantor_session_id(null) — 完整输出
bodies = [
    ('R1 g+gsid=null', {'g_secret': g, 'grantor_session_id': None}),
    ('R2 仅g', {'g_secret': g}),
    ('R3 g+gsid=空串', {'g_secret': g, 'grantor_session_id': ''}),
    ('R4 g+gsid=uuid随机', {'g_secret': g, 'grantor_session_id': '00000000-0000-4000-8000-000000000000'}),
]
for name, bd in bodies:
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', bd, base())
    sc = h.get('set-cookie', '')
    print(f'{name}: {s} body={b[:300]}')
    print(f'   Set-Cookie: {sc[:400]}')
    print()

# 3. 若 202/200: 用 Set-Cookie 验证身份
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
               {'g_secret': g, 'grantor_session_id': None}, base())
scs = h.get('set-cookie', '')
if s in (200, 202):
    # 收集全部 set-cookie 拼会话
    allc = scs
    print('redeem OK, checking identity...')
    s2, h2, b2 = call('https://www.figma.com/api/user/state', 'GET', None,
                      {'Cookie': allc, 'User-Agent': UA, 'Origin': 'https://www.figma.com'})
    print('identity check:', s2, b2[:300])
