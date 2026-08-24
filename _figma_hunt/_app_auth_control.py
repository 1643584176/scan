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
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
A_UID = '1666382703778278399'
B_UID = '1667396392129259941'

def flow(cookie, uid, label):
    base = {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}
    s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
    aid = json.loads(b)['meta']['id']
    s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
                   {**base, 'X-Figma-User-ID': uid})
    g = json.loads(b).get('meta', {}).get('g_secret')
    print(f'[{label}] grant({uid}): {s} g_secret={g}')
    if g:
        # redeem 匿名
        s2, h2, b2 = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
                          {'g_secret': g},
                          {'Content-Type': 'application/json', 'User-Agent': UA,
                           'Origin': 'https://www.figma.com'})
        print(f'[{label}] anon redeem: {s2} {b2[:200]}')
        if s2 == 200:
            sc = [v[:120] for k, v in h2.items() if k.lower() == 'set-cookie']
            print(f'[{label}] SET-COOKIE: {sc}')

flow(AC, A_UID, 'A-cookie grant A_UID')
flow(BC, B_UID, 'B-cookie grant B_UID')
flow(BC, A_UID, 'B-cookie grant A_UID')
