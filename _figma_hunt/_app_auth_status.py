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
base = {'Cookie': AC, 'Content-Type': 'application/json',
        'Origin': 'https://www.figma.com', 'User-Agent': UA,
        'Referer': 'https://www.figma.com/'}

# 用之前的 app_auth id 查状态 (28f99f90-6c0a-45db-8ddf-b1326b4820c1 已 grant)
for aid in ['28f99f90-6c0a-45db-8ddf-b1326b4820c1']:
    for path in [f'/api/session/app_auth/{aid}', f'/api/session/app_auth/{aid}/status']:
        s, h, b = call('https://www.figma.com' + path, 'GET', None, base)
        print(path, ':', s, b[:300])
    print()
