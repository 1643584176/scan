import io, json, urllib.request, urllib.error, re

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

# B 创建
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
aid = json.loads(b)['meta']['id']
print('create:', aid)

# GET grant 页面 (grant 前)
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': BC, 'User-Agent': UA})
m = re.search(r'app_auth_users[^]]{0,400}', b)
print('BEFORE grant: users =', m.group(0)[:300] if m else 'N/A')
m2 = re.search(r'grantor[^,}]{0,100}', b)
print('BEFORE grant: grantor =', m2.group(0)[:120] if m2 else 'N/A')

# B POST grant with A_UID
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base, 'X-Figma-User-ID': A_UID})
g = json.loads(b)['meta']['g_secret']
print('POST grant(A_UID):', s, 'g_secret=', g[:8], '...')

# GET grant 页面 (grant 后)
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': BC, 'User-Agent': UA})
m = re.search(r'app_auth_users[^]]{0,400}', b)
print('AFTER grant: users =', m.group(0)[:300] if m else 'N/A')
for pat in ['grantor', 'appAuthGSecret', 'app_auth_g_secret', 'redirectUrl', 'revoke']:
    mm = re.search(pat + r'[^,}\]]{0,120}', b)
    if mm:
        print(f'AFTER: {pat} =', mm.group(0)[:150])
