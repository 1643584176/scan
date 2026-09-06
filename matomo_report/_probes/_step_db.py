# -*- coding: utf-8 -*-
"""Single-step POST databaseSetup and dump error messages."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]
op.timeout = 120

# 1) GET form first (init session + defaults)
r = op.open(BASE + 'index.php?module=Installation&action=databaseSetup', timeout=120)
body = r.read().decode('utf-8', 'replace')
print('GET len', len(body))

# 2) POST with correct adapter value
fields = {
    'type': 'InnoDB', 'host': '127.0.0.1:3307', 'username': 'matomo',
    'password': 'matomo', 'dbname': 'matomo', 'tables_prefix': 'matomo_',
    'adapter': 'MYSQLI', 'schema': 'Mariadb', 'submit': 'Next',
}
enc = urllib.parse.urlencode(fields).encode()
req = urllib.request.Request(BASE + 'index.php?module=Installation&action=databaseSetup', data=enc)
try:
    resp = op.open(req, timeout=180)
    b2 = resp.read().decode('utf-8', 'replace')
    print('POST ->', resp.status, 'URL:', resp.geturl(), 'len:', len(b2))
except urllib.error.HTTPError as e:
    b2 = e.read().decode('utf-8', 'replace')
    print('POST -> HTTP', e.code, 'len:', len(b2))
except Exception as e:
    print('POST EXC:', type(e).__name__, e)
    raise SystemExit(1)

open(r'F:\scan\matomo_report\_probes\_db_post2.html', 'w', encoding='utf-8').write(b2)
# alerts
for mm in re.finditer(r'<div class="alert alert-(danger|warning)">(.*?)</div>', b2, re.S):
    print('ALERT', mm.group(1), ':', re.sub(r'<[^>]+>|\s+', ' ', mm.group(2)).strip()[:500])
t = re.search(r'<h2>(.*?)</h2>', b2, re.S)
print('H2:', t.group(1)[:150] if t else 'none')
# config written?
import os
cfg = r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php'
if os.path.exists(cfg):
    c = open(cfg, encoding='utf-8', errors='replace').read()
    print('CONFIG HAS database:', '[database]' in c)
