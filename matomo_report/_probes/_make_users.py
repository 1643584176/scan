# -*- coding: utf-8 -*-
"""Create site2 + low-priv user2 (site2 view) + user3 (nothing)."""
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

# 1) second site
r1 = api('SitesManager.addSite', siteName='Site Two', urls='http://site2.local')
print('addSite site2:', r1)

# 2) user2 + user3
r2 = api('UsersManager.addUser', userLogin='user2', password='User2@LocalTest!2026',
         email='xxbo+user2@wearehackerone.com')
print('addUser user2:', r2)
r3 = api('UsersManager.addUser', userLogin='user3', password='User3@LocalTest!2026',
         email='xxbo+user3@wearehackerone.com')
print('addUser user3:', r3)

# 3) grant user2 view on site2 (idSite from addSite result)
if isinstance(r1, int):
    r4 = api('UsersManager.setUserAccess', userLogin='user2', access='view',
             idSites=str(r1))
    print('setUserAccess user2@site%d:' % r1, r4)

# 4) sanity: users list as superuser
r5 = api('UsersManager.getUsers')
print('users:', [u['login'] for u in r5] if isinstance(r5, list) else r5)
r6 = api('SitesManager.getAllSites')
print('sites:', [(s['idsite'], s['name']) for s in r6] if isinstance(r6, list) else r6)
