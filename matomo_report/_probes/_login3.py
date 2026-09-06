# -*- coding: utf-8 -*-
"""Login with exact form fields."""
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
nonce = re.search(r'name="form_nonce"[^>]*value="([^"]*)"', b)
nonce = nonce.group(1) if nonce else ''
print('nonce:', nonce)

data = {
    'form_nonce': nonce,
    'form_login': 'admin',
    'form_password': 'M@tomoLocalTest!2026',
    'form_rememberme': '1',
    'form_redirect': '',
}
b2, u2, s2 = fetch('index.php?module=Login', data)
print('POST login:', s2, len(b2), '->', u2[:120])

# API checks
for method in ['API.getMatomoVersion', 'UsersManager.getUsers', 'SitesManager.getSitesWithAtLeastViewAccess']:
    b3, u3, s3 = fetch('index.php?module=API&method=' + method + '&format=json')
    print('API', method, ':', b3[:300])
