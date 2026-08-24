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

# 用户抓的真实 A cookie
AC = 'DID; product_locale=%22en%22; tatari-session-cookie=0566c723-c243-559c-99b4-ad397fd213b2; __Host-figma.authn=%7B%221666382703778278399%22%3A%22figtkn.5597008061.authn.3fRklqiI60cQqqvEq6Pcjj%22%7D; __Host-figma.authn.mac=1.eyJwbGFuIjoic3RhcnRlciIsImV4cGlyZXNfYXQiOjE3OTIxMTk5MDl9.855950947f1346b381d160b165f0756ad699e485594de2ed6233f74b1c520d63; __Host-figma.embed=%7B%221666382703778278399%22%3A%22figtkn.5597008062.embed.b3rCBzN9t6q0SSSQgfEDOR%22%7D; __Host-figma.embed.mac=1.eyJwbGFuIjoic3RhcnRlciIsImV4cGlyZXNfYXQiOjE3OTIxMTk5MDl9.9d56f33305c5b3f0e3fdb437389a0446b97848d42777313c0a753af215e9d132; figma.session=BAh7CUkiD3Nlc3Npb25faWQGOgZFVG86HVJhY2s6OlNlc3Npb246OlNlc3Npb25JZAY6D0BwdWJsaWNfaWRJIkVkZWUxM2VmYzVkMzhhZTRhYTcyMTAwODU2ZjhhMWMwYjQ4MzBkZmU2MmNiNjQ0ODIwMTI2MGY1ODdlOTJkNzM4BjsARkkiCmZsYXNoBjsARnsASSINdXNlcm5hbWUGOwBGSSIWMTY0MzU4NDE3NkBxcS5jb20GOwBUSSIJY29udAY7AEZJIlAvYXBwX2F1dGgvM2QzZDIyNmUtOWMyYy00ZDhiLWIzNzYtODk4OTE0Mjk3YjcwL2dyYW50P2Rlc2t0b3BfcHJvdG9jb2w9ZmlnbWEGOwBU--20276297b41463151de4510fe72ebb797a75967b; figma.auth_id=ffpa_YmM2OTY1ZjUtOGIwMC00MmI2LTgyZDUtMGQwNTdmMTgzNzZhOjcwM2ZmNDNlNWQwZTU5YWZmZmMzNjk3ZjQxOGJmNDg1MjQ5OTgyODgyZmNkZTJjODhjODI1MGY5MjZjNzc3MDg; IP_ADDRESS_CONTROLS=hLzMewya8EpK0PYheGtNPn-wjJv2N5Os.QfIYN0tSNESHuUiI_l9MOz2BePD5Njb1tttBv_49rXvV7G6qs_v7kqN5KhVmIY3QZ75WOoz0iSUzuwy-uOiWWKkxms8beyZMuf6nsihpfmBnxBZf8j9DiOQZzs3Osg%3D%3D'
# 用用户真实 cookie 完整重放太复杂，先试最小集: authn + session + did 占位(用我们现有的 A cookie 文件)
import re
real = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
print('existing A cookie ok:', len(real) > 100)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
A_UID = '1666382703778278399'
AID = '3d3d226e-9c2c-4d8b-b376-898914297b70'

# 用现有 A cookie + 真实 headers 结构
base = {'Cookie': real, 'Content-Type': 'application/json',
        'Origin': 'https://www.figma.com', 'User-Agent': UA,
        'Referer': f'https://www.figma.com/app_auth/{AID}/grant?desktop_protocol=figma',
        'x-csrf-bypass': 'yes', 'x-figma-client-version': 'b7e40cb988dc4fb3ecfa0accbbd18cb16ff8a143',
        'X-Figma-User-ID': A_UID, 'tsid': 'HZVAML3g2S7I1Nja'}

# 1. A 再 grant (带真实 headers)
s, h, b = call(f'https://www.figma.com/api/session/app_auth/{AID}/grant', 'POST', None, base)
print('A grant with real headers:', s, b[:300])
g = None
try:
    g = json.loads(b)['meta']['g_secret']
    print('g_secret:', g)
except Exception:
    pass

# 2. redeem (带同样 headers)
if g:
    s, h, b = call('https://www.figma.com/api/session/app_auth/redeem', 'POST',
                   {'g_secret': g}, base)
    print('A redeem:', s, b[:400])
    sc = [v[:150] for k, v in h.items() if k.lower() == 'set-cookie']
    print('Set-Cookie:', sc)
