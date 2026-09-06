# -*- coding: utf-8 -*-
"""Browser-equivalent POST to setupSuperUser: exact values incl checkbox/submit."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

# 1) GET form
r = op.open(BASE + 'index.php?module=Installation&action=setupSuperUser')
body = r.read().decode('utf-8', 'replace')
open(r'F:\scan\matomo_report\_probes\_su_get.html', 'w', encoding='utf-8').write(body)

fm = re.search(r'<form\b[^>]*>', body)
end = body.find('</form>', fm.end())
seg = body[fm.end():end]
# dump raw inputs with exact attrs
for m in re.finditer(r'<input\b[^>]*>', seg):
    print('IN:', m.group(0)[:200])

# 2) POST exact-browser style
data = {
    'login': 'admin',
    'password': 'M@tomoLocalTest!2026',
    'password_bis': 'M@tomoLocalTest!2026',
    'email': 'xxbo+matomo@wearehackerone.com',
    'subscribe_newsletter_piwikorg': '1',
    'subscribe_newsletter_professionalservices': '1',
    'submit': 'Next \xbb',
}
enc = urllib.parse.urlencode(data).encode()
req = urllib.request.Request(BASE + 'index.php?module=Installation&action=setupSuperUser', data=enc)
try:
    rr = op.open(req)
    b2 = rr.read().decode('utf-8', 'replace')
    print('POST ->', rr.status, 'URL:', rr.geturl())
except urllib.error.HTTPError as e:
    b2 = e.read().decode('utf-8', 'replace')
    print('POST -> HTTP', e.code, 'URL:', e.geturl())
open(r'F:\scan\matomo_report\_probes\_su_post2.html', 'w', encoding='utf-8').write(b2)
print('len', len(b2))
# what h2 / content?
i = b2.find('content')
for kw in ['Installation_SuperUser', 'Super User', 'Welcome', 'firstWebsiteSetup', 'already exists',
           'password', 'alert-danger', 'form_data']:
    j = b2.find(kw)
    print(kw, 'at', j)
