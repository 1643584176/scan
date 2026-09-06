# -*- coding: utf-8 -*-
"""Extract exact login form fields and POST them."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

def fetch(path, data=None, timeout=240):
    if data is not None:
        enc = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(BASE + path, data=enc)
    else:
        req = urllib.request.Request(BASE + path)
    try:
        r = op.open(req, timeout=timeout)
        return r.read().decode('utf-8', 'replace'), r.geturl(), r.status
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace'), e.geturl(), e.code

b, u, s = fetch('index.php?module=Login')
open(r'F:\scan\matomo_report\_probes\_login_page2.html', 'w', encoding='utf-8').write(b)
# dump all form tags inside the login form
fm = re.search(r'<form\b[^>]*>', b)
print('FORM:', fm.group(0)[:300] if fm else None)
if fm:
    end = b.find('</form>', fm.end())
    seg = b[fm.end():end]
    for m in re.finditer(r'<input\b[^>]*>', seg):
        print('IN:', m.group(0)[:160])
    for m in re.finditer(r'<(?:button|select)\b[^>]*>', seg):
        print('EL:', m.group(0)[:160])
