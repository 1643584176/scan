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

AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'
B_UID = '1667396392129259941'
baseB = {'Cookie': BC, 'Content-Type': 'application/json',
         'Origin': 'https://www.figma.com', 'User-Agent': UA,
         'Referer': 'https://www.figma.com/'}

# B 创建 + grant(A_UID)
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, baseB)
aid = json.loads(b)['meta']['id']
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**baseB, 'X-Figma-User-ID': A_UID})
g = json.loads(b)['meta']['g_secret']
print('B create+grant(A_UID):', aid, g[:10], '...')

# A cookie GET grant 页面
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': AC, 'User-Agent': UA})
print('A-cookie GET grant page:', s, 'len', len(b))
for pat in ['app_auth_g_secret', 'app_auth_users', 'grantor_session', 'redirectUrl', 'app_auth_id']:
    mm = re.search(pat + r'[^,}\]]{0,150}', b)
    if mm:
        print(f'  {pat}:', mm.group(0)[:180])

# B cookie GET grant 页面
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': BC, 'User-Agent': UA})
print('B-cookie GET grant page:', s, 'len', len(b))
for pat in ['app_auth_g_secret', 'app_auth_users', 'grantor_session']:
    mm = re.search(pat + r'[^,}\]]{0,150}', b)
    if mm:
        print(f'  {pat}:', mm.group(0)[:180])
