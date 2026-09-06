# -*- coding: utf-8 -*-
"""Finish installation: walk trackingCode -> finished with warm session."""
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

if __name__ == '__main__':
    # warm session
    b, u, s = fetch('index.php?module=Installation&action=setupSuperUser')
    print('warm setupSuperUser', s, u.split('?')[-1][:50])
    # tracking code
    b, u, s = fetch('index.php?module=Installation&action=trackingCode&site_idSite=1&site_name=Local%20Test%20Site')
    print('GET trackingCode', s, len(b), u.split('?')[-1][:60])
    open(r'F:\scan\matomo_report\_probes\_tracking.html', 'w', encoding='utf-8').write(b)
    # finished
    b, u, s = fetch('index.php?module=Installation&action=finished')
    print('GET finished', s, len(b), u[:120])
    open(r'F:\scan\matomo_report\_probes\_finished.html', 'w', encoding='utf-8').write(b)
    # verify installed: config marker
    import os
    cfg = r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php'
    if os.path.exists(cfg):
        c = open(cfg, encoding='utf-8', errors='replace').read()
        print('config [General]:', re.sub(r'\n+', ' | ', c.split('[database]')[0])[:400])
