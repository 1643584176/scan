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

def base():
    return {'Cookie': AC, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}

# 1. create 完整响应
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base())
print('1. create:', s, b[:500])
meta = json.loads(b)['meta']
aid = meta['id']
print()

# 2. grant 完整响应 (看 grantor_session_id)
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(), 'X-Figma-User-ID': A_UID})
print('2. grant:', s, b[:600])
gmeta = json.loads(b).get('meta', {})
g = gmeta.get('g_secret')
gsid = gmeta.get('grantor_session_id')
print('   g_secret:', g)
print('   grantor_session_id:', gsid)
print()

# 3. redeem: 用 grant 响应的 grantor_session_id
if g:
    for gsid_v in [gsid, None]:
        bd = {'g_secret': g}
        if gsid_v is not None:
            bd['grantor_session_id'] = gsid_v
        s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', bd,
                       {**base(), 'X-Figma-User-ID': A_UID,
                        'Referer': f'https://www.figma.com/app_auth/{aid}/grant?desktop_protocol=figma'})
        sc = [v[:200] for k, v in h.items() if k.lower() == 'set-cookie']
        print(f'3. redeem gsid={gsid_v}:', s, repr(b[:200]))
        if sc:
            print('   Set-Cookie:', sc)
