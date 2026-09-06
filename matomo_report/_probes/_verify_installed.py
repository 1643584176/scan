# -*- coding: utf-8 -*-
"""Verify installation complete: root URL should no longer be installer."""
import http.cookiejar
import re
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

r = op.open(BASE + 'index.php')
b = r.read().decode('utf-8', 'replace')
print('status', r.status, 'len', len(b))
open(r'F:\scan\matomo_report\_probes\_root_after.html', 'w', encoding='utf-8').write(b)
t = re.search(r'<title>(.*?)</title>', b, re.S)
print('TITLE:', t.group(1)[:200] if t else 'none')
for kw in ['Login', 'login', 'Dashboard', 'Installation', 'Sign in', 'Matomo']:
    i = b.find(kw)
    if i >= 0:
        print(kw, 'at', i)
# check config installed marker
import os
cfg = r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php'
c = open(cfg, encoding='utf-8', errors='replace').read()
print('--- config ---')
print(c[:2000])
