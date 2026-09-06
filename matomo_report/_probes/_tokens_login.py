# -*- coding: utf-8 -*-
"""Login as user2/user3, create their tokens."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'

def make_opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [('User-Agent', 'Mozilla/5.0')]
    return op, cj

def fetch(op, path, data=None, timeout=240):
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

def login_and_token(user, pw):
    op, cj = make_opener()
    b, u, s = fetch(op, 'index.php?module=Login')
    m = re.search(r'name="form_nonce"[^>]*value="([^"]*)"', b)
    nonce = m.group(1) if m else ''
    b2, u2, s2 = fetch(op, 'index.php?module=Login',
                        {'form_nonce': nonce, 'form_login': user,
                         'form_password': pw, 'form_rememberme': '1'})
    q = urllib.parse.urlencode({
        'module': 'API', 'method': 'UsersManager.createAppSpecificTokenAuth',
        'userLogin': user, 'description': 'cli-' + user,
        'passwordConfirmation': pw, 'format': 'json'})
    b3, u3, s3 = fetch(op, 'index.php?' + q)
    return s2, u3[:80], b3

for user, pw in [('user2', 'User2@LocalTest!2026'), ('user3', 'User3@LocalTest!2026')]:
    s, u, tok = login_and_token(user, pw)
    print(user, 'login:', s, u)
    print('  token resp:', tok[:300])
