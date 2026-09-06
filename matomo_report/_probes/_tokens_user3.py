# -*- coding: utf-8 -*-
"""Mint token for user3 (login as user3 -> createAppSpecificTokenAuth)."""
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'


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


def main():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [('User-Agent', 'Mozilla/5.0')]

    b, u, s = fetch(op, 'index.php?module=Login')
    m = re.search(r'name="form_nonce"[^>]*value="([^"]*)"', b)
    nonce = m.group(1) if m else 'NONONCE'
    b2, u2, s2 = fetch(op, 'index.php?module=Login',
                       {'form_nonce': nonce, 'form_login': 'user3',
                        'form_password': 'User3@LocalTest!2026', 'form_rememberme': '1'})
    print('user3 login:', s2, u2[:120])

    q = urllib.parse.urlencode({
        'module': 'API', 'method': 'UsersManager.createAppSpecificTokenAuth',
        'userLogin': 'user3', 'description': 'cli-user3',
        'passwordConfirmation': 'User3@LocalTest!2026', 'format': 'json'})
    b3, u3, s3 = fetch(op, 'index.php?' + q)
    print('token resp:', s3, b3[:300])

    # also confirm admin still OK (sanity for matrix later)
    q = urllib.parse.urlencode({
        'module': 'API', 'method': 'UsersManager.getUsers',
        'format': 'json', 'token_auth': 'c3bf071d7f0db740a6f4c60c6affcfd5'})
    b4, u4, s4 = fetch(op, 'index.php?' + q)
    print('admin getUsers:', s4, b4[:200])


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
