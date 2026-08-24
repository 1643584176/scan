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

def base(cookie=AC, uid=A_UID, referer='https://www.figma.com/'):
    return {'Cookie': cookie, 'Content-Type': 'application/json',
            'Origin': 'https://www.figma.com', 'User-Agent': UA,
            'Referer': referer}

# 1. create: 打印完整 meta
s, h, b = call('https://www.figma.com/api/session/app_auth', 'POST', {'app_type': 'desktop'}, base())
meta = json.loads(b)['meta']
aid = meta['id']
print('1. create meta:', json.dumps(meta)[:400])
print()

# 2. grant: 打印完整响应
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{aid}/grant', 'POST', None,
               {**base(), 'X-Figma-User-ID': A_UID})
print('2. grant:', s, b[:400])
g = json.loads(b)['meta']['g_secret']
print('   g_secret:', g)
print()

# 3. redeem 变体矩阵
variants = {
    'A 标准(带cookie+uid)': base(uid=A_UID),
    'B 无cookie匿名': {'Content-Type': 'application/json', 'User-Agent': UA, 'Origin': 'https://www.figma.com'},
    'C 带grantor_session_id': None,  # 下方构造
    'D 无UID头': base(),
}
for name, hd in variants.items():
    if name == 'C':
        bd = {'g_secret': g, 'grantor_session_id': meta.get('grantor_session_id')}
        hd = base(uid=A_UID)
    else:
        bd = {'g_secret': g}
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', bd, hd)
    sc = [v[:120] for k, v in h.items() if k.lower() == 'set-cookie']
    print(f'3.{name}: {s} {b[:200]}')
    if sc:
        print('   Set-Cookie:', sc)
print()

# 4. 先 clear_cont 再 redeem
s, h, b = call('https://www.figma.com/api/session/clear_cont', 'POST', None, base())
print('4. clear_cont:', s, b[:200])
s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST', {'g_secret': g}, base(uid=A_UID))
print('   redeem after clear_cont:', s, b[:200])
