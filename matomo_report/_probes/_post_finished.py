# -*- coding: utf-8 -*-
"""POST the finished form to mark installation complete."""
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

# warm session through the step flow
b, u, s = fetch('index.php?module=Installation&action=setupSuperUser')
print('warm:', s, u.split('?')[-1][:60])
# find the actual submit label on finished page
b, u, s = fetch('index.php?module=Installation&action=finished')
print('GET finished:', s, len(b))
m = re.search(r'name="submit"[^>]*value="([^"]*)"', b)
label = m.group(1) if m else 'Continue \xbb'
print('submit label:', repr(label))
# POST
b2, u2, s2 = fetch('index.php?module=Installation&action=finished',
                   {'submit': label})
print('POST finished:', s2, len(b2), '->', u2[:130])
open(r'F:\scan\matomo_report\_probes\_finish_post.html', 'w', encoding='utf-8').write(b2)
