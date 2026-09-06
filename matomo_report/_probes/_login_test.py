# -*- coding: utf-8 -*-
"""Login as admin via web form, then call API to confirm + get token."""
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

# 1) GET login page, extract form-nonce
b, u, s = fetch('index.php?module=Login')
open(r'F:\scan\matomo_report\_probes\_login_page.html', 'w', encoding='utf-8').write(b)
m = re.search(r'form-nonce="(?:&quot;)?([a-f0-9]+)', b)
nonce = m.group(1) if m else None
print('nonce:', nonce)
m2 = re.search(r'name="(?:login_name|form_nonce|password)"[^>]*value="([^"]*)"', b)

# 2) POST login
data = {
    'module': 'Login',
    'action': 'login',
    'form_nonce': nonce or '',
    'login_name': 'admin',
    'password': 'M@tomoLocalTest!2026',
}
b2, u2, s2 = fetch('index.php', data)
print('POST login:', s2, len(b2), '->', u2[:130])

# 3) API test with session
b3, u3, s3 = fetch('index.php?module=API&method=API.getMatomoVersion&format=json')
print('API version:', b3[:200])

# 4) try to grab token_auth from user
b4, u4, s4 = fetch('index.php?module=API&method=UsersManager.getUser&format=json')
print('API getUser:', b4[:400])
