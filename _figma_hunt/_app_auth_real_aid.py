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

def base(uid=A_UID):
    return {'Cookie': AC, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}

# 用户真实流程的 aid (figma.session 中的 grant URL)
AID = '3d3d226e-9c2c-4d8b-b376-898914297b70'

# 1. 重新 grant
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{AID}/grant', 'POST', None, base())
print('1. grant 3d3d226e:', s, b[:250])
g = None
try:
    g = json.loads(b)['meta']['g_secret']
    print('   g_secret:', g)
except Exception as e:
    print('   no g_secret:', b[:200])

# 2. redeem (带完整 headers, 模拟页面)
if g:
    hd = {**base(), 'X-Figma-User-ID': A_UID,
          'Referer': f'https://www.figma.com/app_auth/{AID}/grant?desktop_protocol=figma'}
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', {'g_secret': g}, hd)
    sc = [v[:250] for k, v in h.items() if k.lower() == 'set-cookie']
    print('2. redeem:', s, repr(b[:300]))
    print('   Set-Cookie:', sc)

    # 3. 若成功, 用新会话查身份
    if s in (200, 202):
        newc = '; '.join(sc)
        s2, h2, b2 = call('https://www.figma.com/api/user/state', 'GET', None,
                          {'Cookie': newc, 'User-Agent': UA, 'Origin': 'https://www.figma.com'})
        print('3. identity:', s2, b2[:250])
