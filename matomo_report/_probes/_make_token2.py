# -*- coding: utf-8 -*-
"""Create app token (with password confirmation)."""
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

b, u, s = fetch('index.php?module=Login')
nonce = re.search(r'name="form_nonce"[^>]*value="([^"]*)"', b).group(1)
data = {'form_nonce': nonce, 'form_login': 'admin',
        'form_password': 'M@tomoLocalTest!2026', 'form_rememberme': '1'}
b2, u2, s2 = fetch('index.php?module=Login', data)
print('login:', s2)

b3, u3, s3 = fetch('index.php?module=API&method=UsersManager.createAppSpecificTokenAuth'
                   '&userLogin=admin&description=cli-test&passwordConfirmation=M%40tomoLocalTest%212026&format=json')
print('create token:', b3[:300])
open(r'F:\scan\matomo_report\_probes\_token_resp.json', 'w').write(b3)
