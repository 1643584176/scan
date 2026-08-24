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

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'
B_UID = '1667396392129259941'
# A_UID grant 的 g_secret（上一步拿到）
G_SECRET = 'VI42IYdv8vDN8ZiWLr55BuMDfpHrSD4lX'

# 匿名 redeem（g_secret 是 bearer 凭证，redeem 不应需要 cookie）
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
               {'g_secret': G_SECRET},
               {'Content-Type': 'application/json', 'User-Agent': UA,
                'Origin': 'https://www.figma.com'})
print('anonymous redeem:', s)
print(b[:800])
print()
# 找 Set-Cookie
for k, v in h.items():
    if k.lower() == 'set-cookie':
        print('Set-Cookie:', v[:300])
