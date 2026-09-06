# -*- coding: utf-8 -*-
"""Create tokens for user2/user3 via superuser (try admin password confirmation)."""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOK = 'c3bf071d7f0db740a6f4c60c6affcfd5'

def api(method, **params):
    q = urllib.parse.urlencode(dict(params, module='API', method=method,
                                    format='json', token_auth=TOK))
    req = urllib.request.Request(BASE + 'index.php?' + q)
    try:
        r = urllib.request.urlopen(req, timeout=180)
        return json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        return {'http_error': e.code, 'body': e.read().decode('utf-8', 'replace')[:300]}

# try superuser creating for user2 with its own password confirmation
for u, pw in [('user2', 'User2@LocalTest!2026'), ('user3', 'User3@LocalTest!2026')]:
    r = api('UsersManager.createAppSpecificTokenAuth', userLogin=u,
            description='cli-' + u,
            passwordConfirmation=pw)
    print(u, '->', str(r)[:300])
