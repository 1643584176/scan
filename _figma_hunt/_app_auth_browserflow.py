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
base = {'Cookie': AC, 'Content-Type': 'application/json',
        'Origin': 'https://www.figma.com', 'User-Agent': UA,
        'Referer': 'https://www.figma.com/'}

# 1. create
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
aid = json.loads(b)['meta']['id']
print('1. create:', aid)

# 2. GET grant 页面 (浏览器加载)
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': AC, 'User-Agent': UA})
print('2. GET grant page:', s, 'len', len(b))

# 3. POST grant
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base, 'X-Figma-User-ID': A_UID})
print('3. POST grant:', s, b[:250])
g = json.loads(b).get('meta', {}).get('g_secret')

# 4. redeem
if g:
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
                   {'g_secret': g},
                   {'Cookie': AC, 'Content-Type': 'application/json', 'User-Agent': UA,
                    'Origin': 'https://www.figma.com'})
    print('4. redeem:', s, b[:300])
    sc = [v[:200] for k, v in h.items() if k.lower() == 'set-cookie']
    print('   Set-Cookie:', sc)
