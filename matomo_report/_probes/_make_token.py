# -*- coding: utf-8 -*-
"""Login then create app-specific token via session-authed API."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

def fetch(path, data=None, timeout=240):
    if data is not None:
        enc = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(BASE + path, data=enc)
    else:
        req = urllib.request.Request(BASE + path)
    try:
        r = op.open(req, timeout=timeout)
        return r.read().decode('utf-8', 'replace'), r.geturl(), r.status
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace'), e.geturl(), e.code

# login
b, u, s = fetch('index.php?module=Login')
nonce = re.search(r'name="form_nonce"[^>]*value="([^"]*)"', b).group(1)
data = {'form_nonce': nonce, 'form_login': 'admin',
        'form_password': 'M@tomoLocalTest!2026', 'form_rememberme': '1'}
b2, u2, s2 = fetch('index.php?module=Login', data)
print('login:', s2, '->', u2.split('?')[1][:60] if '?' in u2 else u2[:60])

# call API (session-authed?)
b3, u3, s3 = fetch('index.php?module=API&method=UsersManager.createAppSpecificTokenAuth'
                   '&userLogin=admin&description=cli-test&format=json')
print('create token:', b3[:300])
