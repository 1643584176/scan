# -*- coding: utf-8 -*-
"""POST firstWebsiteSetup WITHOUT auto-redirect: capture raw 302 Location."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print('REDIRECT', code, '->', newurl)
        return None  # do not follow

op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), NoRedirect())
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

def get(path):
    try:
        r = op.open(BASE + path)
        return r.read().decode('utf-8', 'replace'), r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace'), e.code, dict(e.headers)

def post(path, data):
    enc = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=enc)
    try:
        r = op.open(req)
        return r.read().decode('utf-8', 'replace'), r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace'), e.code, dict(e.headers)

if __name__ == '__main__':
    # fresh walk: db->su already done in DB; go straight: get superuser page to init session state,
    # then firstWebsiteSetup GET + POST raw.
    b, s, h = get('index.php?module=Installation&action=setupSuperUser')
    print('GET setupSuperUser', s, len(b))
    # because superuser exists, this should redirect to next step (firstWebsiteSetup)
    b, s, h = get('index.php?module=Installation&action=firstWebsiteSetup')
    print('GET firstWebsiteSetup', s, len(b))
    fm = re.search(r'<form\b[^>]*>', b)
    if not fm:
        print('NO FORM')
        raise SystemExit(1)
    m = re.search(r'action="([^"]*)"', fm.group(0))
    action = m.group(1)
    print('action:', action)
    # find submit value
    sv = re.search(r'name="submit"[^>]*value="([^"]*)"', b)
    print('submit value:', sv.group(1) if sv else None)
    # find timezone select options sample + selected
    tz = re.search(r'name="timezone".*?</select>', b, re.S)
    if tz:
        opts = re.findall(r'value="([^"]*)"', tz.group(0))
        print('tz opts count', len(opts), 'first:', opts[:3], 'has UTC:', 'UTC' in opts)
    data = {
        'siteName': 'Local Test Site',
        'url': 'http://127.0.0.1:8080/',
        'timezone': 'UTC',
        'ecommerce': '0',
        'submit': 'Next \xbb',
    }
    b2, s2, h2 = post('index.php?module=Installation&action=firstWebsiteSetup', data)
    print('POST ->', s2, len(b2))
    loc = h2.get('Location') or h2.get('location')
    print('Location:', loc)
    open(r'F:\scan\matomo_report\_probes\_fws_raw.html', 'w', encoding='utf-8').write(b2)
