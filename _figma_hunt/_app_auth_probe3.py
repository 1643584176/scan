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

base = {'Cookie': BC, 'Content-Type': 'application/json',
        'Origin': 'https://www.figma.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36',
        'Referer': 'https://www.figma.com/'}

# 变体 1-4: app_type
for t in ['desktop', 'vscode', 'figma-desktop', 'browser']:
    s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': t}, base)
    print(f'app_type={t}: {s} body={b[:150]}')

# 变体 5: 无 body
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', None, base)
print(f'no body: {s} body={b[:150]}')

# 变体 6: grant 页面 GET
s, h, b = call('https://www.figma.com/app_auth/abc123/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': BC, 'User-Agent': base['User-Agent']})
print(f'grant page: {s} len={len(b)} first={b[:100]!r}')
