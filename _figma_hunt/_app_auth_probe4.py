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

aid = 'f6ecae55-5d93-4549-bcf2-b7f47adef277'  # B 的 desktop app_auth
# grant 页面
s, h, b = call(f'https://www.figma.com/app_auth/{aid}/grant', 'GET', None,
               {'Cookie': BC, 'User-Agent': UA})
print('grant page:', s, 'len', len(b))
# 找 g_secret 相关初始状态
import re
for pat in ['app_auth_g_secret', 'g_secret', 'grantor_session_id', 'app_auth_users', 'redeem']:
    for m in re.finditer(pat, b):
        i = m.start()
        print(f'--- {pat} ---')
        print(b[max(0,i-150):i+250].replace('\n', ' ')[:400])
        break
