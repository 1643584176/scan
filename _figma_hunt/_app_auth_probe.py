import io, json, urllib.request, urllib.error

def call(url, method='GET', body=None, headers=None, timeout=20):
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        raw = r.read()
        return r.status, r.headers, raw.decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode(errors='replace')
    except Exception as e:
        return -1, None, str(e)

AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

# 1. B 带 cookie 发起 app_auth
s, h, body = call('https://www.figma.com/api/session/app_auth',
                  'POST', {'app_type': 'desktop'},
                  {'Cookie': BC, 'Content-Type': 'application/json'})
print('B cookie app_auth:', s)
print(body[:600])
