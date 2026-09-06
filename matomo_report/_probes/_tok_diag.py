# -*- coding: utf-8 -*-
"""Login as user2, create token - with full exception surfacing."""
import http.cookiejar
import re
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'

def run():
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
    print('GET login:', s, len(b))
    m = re.search(r'name="form_nonce"[^>]*value="([^"]*)"', b)
    nonce = m.group(1) if m else 'NONONCE'
    print('nonce:', nonce)
    b2, u2, s2 = fetch('index.php?module=Login',
                       {'form_nonce': nonce, 'form_login': 'user2',
                        'form_password': 'User2@LocalTest!2026', 'form_rememberme': '1'})
    print('POST login:', s2, len(b2), u2[:100])
    # where did we land?
    if 'Login' in u2 and 'index' not in u2:
        # check login errors on page
        for mm in re.finditer(r'<div class="[^"]*alert[^"]*">(.*?)</div>', b2, re.S)[:3]:
            print('ALERT:', re.sub(r'<[^>]+>|\s+', ' ', mm.group(1))[:200])
    q = urllib.parse.urlencode({
        'module': 'API', 'method': 'UsersManager.createAppSpecificTokenAuth',
        'userLogin': 'user2', 'description': 'cli-user2',
        'passwordConfirmation': 'User2@LocalTest!2026', 'format': 'json'})
    b3, u3, s3 = fetch('index.php?' + q)
    print('token resp:', s3, b3[:300])

try:
    run()
except Exception:
    traceback.print_exc()
