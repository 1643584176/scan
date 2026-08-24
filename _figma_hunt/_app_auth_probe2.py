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
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

for label, cookie in [('B', BC), ('A', AC)]:
    s, h, body = call('https://www.figma.com/api/session/app_auth',
                      'POST', {'app_type': 'desktop'},
                      {'Cookie': cookie, 'Content-Type': 'application/json'})
    print(f'== {label} {s} ==')
    for k, v in h.items():
        if k.lower() in ('location', 'set-cookie', 'x-figma-*', 'content-type', 'content-length'):
            print(' ', k, ':', v[:200])
    print('body:', body[:200])
    print()
