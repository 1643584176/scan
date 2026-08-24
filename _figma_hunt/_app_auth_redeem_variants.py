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
# A 新授权
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
aid = json.loads(b)['meta']['id']
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base, 'X-Figma-User-ID': A_UID})
g = json.loads(b)['meta']['g_secret']
print('grant ok:', aid, g)

variants = [
    ('body+desktop_protocol', {'g_secret': g, 'desktop_protocol': 'figma'}),
    ('body+app_type', {'g_secret': g, 'app_type': 'desktop'}),
    ('header X-UID', {'g_secret': g}, {'X-Figma-User-ID': A_UID}),
]
for label, body, extra in [ (v[0], v[1], v[2] if len(v) > 2 else {}) for v in variants]:
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', body, {**base, **extra})
    print(f'{label}: {s} {b[:150]}')
