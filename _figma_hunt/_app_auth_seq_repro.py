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

def base(cookie=AC, uid=A_UID):
    return {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': 'https://www.figma.com/'}

# 完整复刻上个脚本序列: create->grant->A(标准)->B(匿名)->C(gsid)->D(无uid)
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base())
meta = json.loads(b)['meta']
aid = meta['id']
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(), 'X-Figma-User-ID': A_UID})
g = json.loads(b)['meta']['g_secret']
print('create+grant:', aid[:8], g[:8], 'gsid=', meta['grantor_session_id'])

# A: 标准 redeem
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', {'g_secret': g}, base(uid=A_UID))
print('A 标准:', s, b[:100])

# B: 匿名
hd = {'Content-Type': 'application/json', 'User-Agent': UA, 'Origin': 'https://www.figma.com'}
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', {'g_secret': g}, hd)
print('B 匿名:', s, b[:100])

# C: gsid=null
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
               {'g_secret': g, 'grantor_session_id': meta.get('grantor_session_id')}, base(uid=A_UID))
print('C gsid:', s, repr(b[:150]))
sc = [v[:200] for k, v in h.items() if k.lower() == 'set-cookie']
print('  Set-Cookie:', sc)

# D: 无uid
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', {'g_secret': g}, base())
print('D 无uid:', s, b[:100])
