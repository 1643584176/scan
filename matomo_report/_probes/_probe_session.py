# -*- coding: utf-8 -*-
"""Probe session persistence: two GETs, compare cookies and set-cookie headers."""
import http.cookiejar
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

for i in range(2):
    r = op.open(BASE + 'index.php?module=Installation&action=setupSuperUser')
    body = r.read().decode('utf-8', 'replace')
    sc = r.headers.get_all('Set-Cookie')
    print('GET', i, 'status', r.status, 'len', len(body))
    print('  set-cookie:', sc)
    print('  jar:', [(c.name, c.value[:20]) for c in cj])

# also check session file dir on disk
import glob, os
for d in [r'F:\scan\matomo_report\_src\matomo-release\matomo\tmp\sessions',
          os.environ.get('TEMP', ''), r'F:\scan\matomo_report\_runtime\php\sessions']:
    try:
        fs = glob.glob(os.path.join(d, 'sess_*'))
        print(d, '->', len(fs), 'session files')
    except Exception as e:
        print(d, 'ERR', e)
