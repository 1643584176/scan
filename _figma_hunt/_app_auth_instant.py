import io, json, urllib.request, urllib.error, time

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
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
A_UID = '1666382703778278399'
B_UID = '1667396392129259941'

def mkbase(cookie, uid, tsid):
    return {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/',
            'x-csrf-bypass': 'yes',
            'x-figma-client-version': 'b7e40cb988dc4fb3ecfa0accbbd18cb16ff8a143',
            'X-Figma-User-ID': uid, 'tsid': tsid}

def flow(cookie, uid, label):
    tsid = 'TST' + str(int(time.time()))
    base = mkbase(cookie, uid, tsid)
    s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base)
    aid = json.loads(b)['meta']['id']
    s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None, base)
    g = json.loads(b).get('meta', {}).get('g_secret')
    print(f'[{label}] create={aid[:8]} grant={s} g={g}')
    if g:
        s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
                       {'g_secret': g}, base)
        print(f'[{label}] redeem={s} body={b[:250]}')
        sc = [v[:150] for k, v in h.items() if k.lower() == 'set-cookie']
        print(f'[{label}] Set-Cookie: {sc}')

flow(BC, A_UID, 'B-cookie grant(A_UID)')
flow(AC, A_UID, 'A-cookie grant(A_UID)')
