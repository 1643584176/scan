# -*- coding: utf-8 -*-
"""Verify user3's minted token identity + login anomaly."""

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'


def api(token, method, **params):
    q = urllib.parse.urlencode(dict(params, module='API', method=method,
                                    format='json', token_auth=token))
    req = urllib.request.Request(BASE + 'index.php?' + q)
    try:
        r = urllib.request.urlopen(req, timeout=120)
        body = r.read().decode('utf-8', 'replace')
        return r.status, body[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:400]


tok3 = 'bfb52eb146d39b0d40c365a46491f589'
tok2 = '794beeb243443742f0df05b4432c734e'
adm = 'c3bf071d7f0db740a6f4c60c6affcfd5'

for label, t in [('user3-token', tok3), ('user2-token', tok2), ('admin', adm)]:
    for method in ['UsersManager.getUser', 'UsersManager.getUsersAccess',
                   'SitesManager.getSitesWithAtLeastViewAccess']:
        s, b = api(t, method)
        print('%s | %s | %s | %s' % (label, method, s, b.replace('\n', ' ')[:300]))
    print('-' * 100)
