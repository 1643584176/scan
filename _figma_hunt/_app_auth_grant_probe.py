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

# 1. B 创建 app_auth
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
meta = json.loads(b)['meta']
aid = meta['id']
print('1. created app_auth:', aid, 'grantor_session_id:', meta['grantor_session_id'])

# 2. B 带自己的 UID grant
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base, 'X-Figma-User-ID': B_UID})
print('2. grant with B UID:', s, b[:300])

# 3. 再建一个，带 A 的 UID grant
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
aid2 = json.loads(b)['meta']['id']
print('3. created app_auth2:', aid2)
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid2}/grant', 'POST', None,
               {**base, 'X-Figma-User-ID': A_UID})
print('4. grant with A UID:', s, b[:300])
