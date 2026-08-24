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

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'
B_UID = '1667396392129259941'
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

def base(cookie):
    return {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}

# 1. B create + grant
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base(BC))
aid = json.loads(b)['meta']['id']
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(BC), 'X-Figma-User-ID': B_UID})
g = json.loads(b)['meta']['g_secret']
print('1. B create+grant:', aid, 'g=', g)
print()

# 2. A cookie GET grant 页面, 搜 g_secret
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'Cookie': AC, 'User-Agent': UA, 'Accept': 'text/html'})
print('2. A GET grant page:', s, 'len=', len(b))
found = g in b
print('   A 页面包含 B 的 g_secret?', found)
if found:
    idx = b.find(g)
    print('   上下文:', b[max(0, idx-300):idx+100][:500])
else:
    # 搜 payload 里 app_auth 相关字段
    for pat in ['app_auth', 'g_secret', 'grantor', 'g_secret', '"id"']:
        for m in re.finditer(pat, b):
            i = m.start()
            print(f'   [{pat}] ...{b[max(0,i-80):i+120]}...')
            break
print()

# 3. 匿名 GET grant 页面
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma', 'GET', None,
               {'User-Agent': UA, 'Accept': 'text/html'})
print('3. 匿名 GET grant page:', s, 'len=', len(b), '含g_secret?', g in b)

# 4. A 也 grant 一次 (看 A 拿到什么)
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(AC), 'X-Figma-User-ID': A_UID})
print('4. A POST grant:', s, b[:250])
