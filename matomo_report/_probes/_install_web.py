# -*- coding: utf-8 -*-
"""Drive Matomo web installer via requests-like urllib (no deps)."""
import http.cookiejar
import re
import sys
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

def get(path, out=None):
    r = op.open(BASE + path)
    body = r.read().decode('utf-8', 'replace')
    print('GET', path, '->', r.status, len(body))
    if out:
        open(out, 'w', encoding='utf-8').write(body)
    return body

def post(path, data, out=None):
    enc = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=enc)
    try:
        r = op.open(req)
        body = r.read().decode('utf-8', 'replace')
        print('POST', path, data.get('action', '') , '->', r.status, len(body))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        print('POST', path, '-> HTTP', e.code, len(body))
    if out:
        open(out, 'w', encoding='utf-8').write(body)
    return body

if __name__ == '__main__':
    import urllib.parse
    # step 0: hit the app, see where it lands
    b = get('', 'F:/scan/matomo_report/_probes/_install_0.html')
    # extract installer action / hidden fields
    for pat in [r'action="([^"]*)"', r'name="([a-zA-Z_]+)"', r'value="([^"]*)"']:
        print(pat, '=>', sorted(set(re.findall(pat, b)))[:40])
