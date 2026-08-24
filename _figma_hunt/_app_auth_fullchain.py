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

BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'
B_UID = '1667396392129259941'
base = {'Cookie': BC, 'Content-Type': 'application/json',
        'Origin': 'https://www.figma.com', 'User-Agent': UA,
        'Referer': 'https://www.figma.com/'}

# 1. create (B cookie)
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
aid = json.loads(b)['meta']['id']
print('1. create:', aid)

# 2. grant with A_UID (B cookie)
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base, 'X-Figma-User-ID': A_UID})
print('2. grant(A_UID):', s, b[:200])
try:
    g = json.loads(b)['meta']['g_secret']
    print('   g_secret:', g)
except Exception:
    g = None

if g:
    # 3. redeem 无 cookie
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
                   {'g_secret': g},
                   {'Content-Type': 'application/json', 'User-Agent': UA,
                    'Origin': 'https://www.figma.com'})
    print('3. anon redeem:', s, b[:300])
    # 3b. redeem 带 B cookie
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
                   {'g_secret': g},
                   {**base})
    print('4. B-cookie redeem:', s, b[:300])
    for k, v in h.items():
        if k.lower() == 'set-cookie':
            print('   Set-Cookie:', v[:150])
