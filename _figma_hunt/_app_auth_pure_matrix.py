import io, json, urllib.request, urllib.error, urllib.parse

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

def make_pure(cookie_file, keep_uid):
    """构造 authn 只含 keep_uid 的纯净 cookie"""
    c = io.open(cookie_file, encoding='utf-8').read().strip().replace('\n', '; ')
    parts = {}
    for p in c.split('; '):
        if '=' in p:
            k, v = p.split('=', 1)
            parts[k] = v
    authn_raw = parts.get('__Host-figma.authn', '')
    authn = json.loads(urllib.parse.unquote(authn_raw))
    authn = {k: v for k, v in authn.items() if k == keep_uid}
    parts['__Host-figma.authn'] = urllib.parse.quote(json.dumps(authn, separators=(',', ':')))
    return '; '.join(f'{k}={v}' for k, v in parts.items())

PURE_B = make_pure('ws_cookie_B_new.txt', B_UID)
PURE_A = make_pure('ws_cookie_A_new.txt', A_UID)
print('PURE_B authn only B:', B_UID in PURE_B and A_UID not in PURE_B)
print('PURE_A authn only A:', A_UID in PURE_A)

def base(cookie):
    return {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}

def create_and_grant(cookie, claim_uid, label):
    s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base(cookie))
    try:
        aid = json.loads(b)['meta']['id']
    except Exception:
        print(f'[{label}] create FAIL: {s} {b[:150]}')
        return
    hd = base(cookie)
    if claim_uid:
        hd['X-Figma-User-ID'] = claim_uid
    s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None, hd)
    g = None
    try:
        g = json.loads(b)['meta']['g_secret']
    except Exception:
        pass
    print(f'[{label}] create={aid[:8]} grant({claim_uid or "无"}): {s} g={g[:12] if g else None} body={b[:120]}')

# 测试矩阵
create_and_grant(PURE_A, A_UID, 'A纯净 claim A')
create_and_grant(PURE_A, None, 'A纯净 无UID头')
create_and_grant(PURE_B, B_UID, 'B纯净 claim B')
create_and_grant(PURE_B, A_UID, 'B纯净 claim A  ← 核心')
create_and_grant(PURE_B, None, 'B纯净 无UID头')

# 匿名 create
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'},
               {'Content-Type': 'application/json', 'Origin': 'https://www.figma.com', 'User-Agent': UA})
print('[匿名 create]:', s, b[:150])
