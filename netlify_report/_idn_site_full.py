# -*- coding: utf-8 -*-
# _idn_site_full.py - full site object dump to file + grep identity/jwt related fields
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

def req(url, tok):
    r = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok})
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        return resp.status, resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')

st, b = req('https://api.netlify.com/api/v1/sites/%s' % SITE_A, TOKEN_A)
print('status', st, 'len', len(b))
with open('_site_full_dump.json', 'w', encoding='utf-8') as f:
    f.write(b)
try:
    j = json.loads(b)
    print('total fields:', len(j))
    for k in sorted(j.keys()):
        if any(s in k.lower() for s in ('identity', 'jwt', 'secret', 'domain', 'password', 'auth', 'token')):
            v = json.dumps(j[k]) if not isinstance(j[k], str) else j[k]
            print('  %s = %s' % (k, v[:400]))
    print('--- all keys:', sorted(j.keys()))
except Exception as e:
    print('parse err', e)
    print(b[:500])
