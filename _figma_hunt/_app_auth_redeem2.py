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
G_SECRET = 'VI42IYdv8vDN8ZiWLr55BuMDfpHrSD4lX'  # A_UID grant 的

# B cookie redeem
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
               {'g_secret': G_SECRET},
               {'Cookie': BC, 'Content-Type': 'application/json', 'User-Agent': UA,
                'Origin': 'https://www.figma.com'})
print('B-cookie redeem:', s)
print(b[:1000])
print()
for k, v in h.items():
    if k.lower() == 'set-cookie':
        print('Set-Cookie:', v[:200])
