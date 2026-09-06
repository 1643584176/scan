# -*- coding: utf-8 -*-
"""Grant user2 view on site2; verify matrix."""
import json
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOK = 'c3bf071d7f0db740a6f4c60c6affcfd5'

def api(method, **params):
    q = urllib.parse.urlencode(dict(params, module='API', method=method,
                                    format='json', token_auth=TOK))
    r = urllib.request.urlopen(BASE + 'index.php?' + q, timeout=180)
    return json.loads(r.read().decode('utf-8', 'replace'))

r = api('UsersManager.setUserAccess', userLogin='user2', access='view', idSites='2')
print('grant:', r)
r2 = api('UsersManager.getUsersAccess', userLogin='user2')
print('user2 access:', r2)
r3 = api('SitesManager.getAllSites')
print('sites:', [(s['idsite'], s['name']) for s in r3] if isinstance(r3, list) else r3)
