import io, json, urllib.request, urllib.error, http.cookiejar

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(url, method='GET', body=None, headers=None, timeout=20):
    req = urllib.request.Request(url, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        r = opener.open(req, timeout=timeout)
        return r.status, dict(r.headers), r.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors='replace')
    except Exception as e:
        return -1, {}, str(e)

# 种子 cookie: 先请求一次 homepage 让 cookie jar 带上
s, h, b = call('https://www.figma.com/', 'GET', None,
               {'Cookie': AC, 'User-Agent': UA})
print('seed homepage:', s)

def merged_cookie():
    # 种子 cookie + jar 中新 set 的 cookie 合并
    jar_c = '; '.join(f'{c.name}={c.value}' for c in cj)
    return (AC + '; ' + jar_c) if jar_c else AC

def base():
    return {'Cookie': merged_cookie(), 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com',
            'User-Agent': UA, 'Referer': 'https://www.figma.com/'}

# 1. create
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base())
meta = json.loads(b)['meta']
aid = meta['id']
print('1. create:', aid)

# 2. GET grant 页面 (模拟浏览器加载, 收集 Set-Cookie)
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'User-Agent': UA, 'Accept': 'text/html'})
sc = h.get('set-cookie', '')
print('2. GET grant page:', s, 'set-cookie:', sc[:300])
print('   page contains login?', 'login' in b[:2000].lower())

# 3. POST grant (页面 JS 行为)
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(), 'X-Figma-User-ID': A_UID})
g = json.loads(b)['meta']['g_secret']
print('3. POST grant:', s, 'g=', g[:10])

# 4. clear_cont (页面 JS 行为)
s, h, b = call('https://www.figma.com/api/session/clear_cont', 'POST', None, base())
print('4. clear_cont:', s)

# 5. redeem (页面收到 postMessage 后)
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
               {'g_secret': g}, base())
sc = [v[:250] for k, v in h.items() if k.lower() == 'set-cookie']
print('5. redeem:', s, repr(b[:300]))
print('   Set-Cookie:', sc)

# 6. 身份验证
if s in (200, 202):
    s2, h2, b2 = call('https://www.figma.com/api/user/state', 'GET', None,
                      {'User-Agent': UA, 'Origin': 'https://www.figma.com'})
    print('6. identity:', s2, b2[:200])
