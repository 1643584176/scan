# -*- coding: utf-8 -*-
"""POST databaseSetup form to Matomo installer."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPRedirectHandler())
op.addheaders = [('User-Agent', 'Mozilla/5.0'),
                 ('X-Requested-With', 'XMLHttpRequest')]

def req(path, data=None):
    if data is not None:
        enc = urllib.parse.urlencode(data).encode()
        r = urllib.request.Request(BASE + path, data=enc)
    else:
        r = urllib.request.Request(BASE + path)
    try:
        resp = op.open(r)
        body = resp.read().decode('utf-8', 'replace')
        print('->', resp.status, 'final URL:', resp.geturl(), 'len:', len(body))
        return body, resp
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        print('-> HTTP', e.code, 'len:', len(body))
        return body, e

if __name__ == '__main__':
    # warm up: GET welcome to init session
    b, _ = req('index.php?module=Installation&action=welcome')
    print('welcome len', len(b), 'cookies:', [c.name for c in cj])
    # try AJAX-ish POST to databaseSetup with form fields
    fields = {
        'host': '127.0.0.1', 'port': '3307', 'username': 'matomo',
        'password': 'matomo', 'dbname': 'matomo', 'tables_prefix': 'matomo_',
        'adapter': 'Mysqli', 'schema': 'Mysql', 'type': 'submit',
        'submit': 'Next',
    }
    b2, _ = req('index.php?module=Installation&action=databaseSetup', fields)
    open(r'F:\scan\matomo_report\_probes\_db_post_out.html', 'w', encoding='utf-8').write(b2)
    # title + hints
    t = re.search(r'<title>(.*?)</title>', b2, re.S)
    print('TITLE:', t.group(1)[:200] if t else 'none')
    for kw in ['error', 'Error', 'exception', 'redirect', 'tablesCreation', 'System', 'success']:
        i = b2.find(kw)
        if i >= 0:
            print(kw, 'at', i, ':', re.sub(r'<[^>]+>|\s+', ' ', b2[max(0, i-100):i+200])[:220])
