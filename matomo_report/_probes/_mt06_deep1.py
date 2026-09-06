# -*- coding: utf-8 -*-
"""Deep-dive: (A) bulk w/ array urls + nested auth probing; (B) getFollowingPages w/
real page URL; (C) anonymous baseline on DATA candidates."""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOKENS = {
    'admin': 'c3bf071d7f0db740a6f4c60c6affcfd5',
    'user2': '794beeb243443742f0df05b4432c734e',
    'user3': 'bfb52eb146d39b0d40c365a46491f589',
    'anon': None,
}


def call(params, timeout=40):
    q = dict(params, module='API', format='json')
    url = BASE + 'index.php?' + urllib.parse.urlencode(q, doseq=True)
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR', str(e)[:150]


print('### A. getBulkRequest with array urls + nested methods')
# A1: user3 (zero rights) bulk-calls UsersManager.getUsers (admin-only) - expect denied inside
nested = urllib.parse.quote('module=API&method=UsersManager.getUsers', safe='')
s, b = call({'method': 'API.getBulkRequest',
             'urls[]': 'module=API&method=API.getSettings',
             'urls[]': 'module=API&method=UsersManager.getUsers',
             'token_auth': TOKENS['user3']})
print('A1 user3 bulk [getSettings,getUsers]:', s, b[:400])

# A2: anon bulk calling authed method with nested token (session-less self-supply path)
s, b = call({'method': 'API.getBulkRequest',
             'urls[]': 'module=API&method=UsersManager.getUsers&token_auth=' + TOKENS['admin']})
print('A2 anon bulk w/ nested admin token:', s, b[:300])

# A3: anon bulk w/o any token -> nested getUsers should fail
s, b = call({'method': 'API.getBulkRequest',
             'urls[]': 'module=API&method=UsersManager.getUsers'})
print('A3 anon bulk no token:', s, b[:300])

# A4: user3 bulk with force_api_session conflict probe
s, b = call({'method': 'API.getBulkRequest', 'force_api_session': '0',
             'urls[]': 'module=API&method=API.getSettings&force_api_session=1'})
print('A4 anon bulk force_api_session conflict:', s, b[:300])

print()
print('### B. Overlay.getFollowingPages with real site1 URL (/home)')
for who, tok in TOKENS.items():
    q = {'method': 'Overlay.getFollowingPages', 'idSite': '1',
         'period': 'day', 'date': 'today',
         'url': 'http://127.0.0.1:8080/home'}
    if tok:
        q['token_auth'] = tok
    s, b = call(q)
    print('B %-6s: %s %s' % (who, s, b[:400]))

print()
print('### C. anonymous baseline on management DATA candidates')
for m, p in [
    ('API.getBulkRequest', {'urls[]': 'module=API&method=API.getSettings'}),
    ('API.getSettings', {}),
    ('API.getPagesComparisonsDisabledFor', {}),
    ('Overlay.getTranslations', {}),
    ('SitesManager.getIpsForRange', {'ipRange': '10.0.0.0/8'}),
    ('LanguagesManager.getAvailableLanguages', {}),
]:
    q = dict(p, method=m)
    s, b = call(q)
    print('C %-40s %s %s' % (m, s, b[:200]))
