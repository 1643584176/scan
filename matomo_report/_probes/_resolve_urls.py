# -*- coding: utf-8 -*-
"""Resolve real download URLs for portable PHP (8.3 x64 NTS) + MariaDB (11.4 winx64)."""
import re
import urllib.request

def get(url, max_bytes=2_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 h1kit/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(max_bytes).decode('utf-8', 'replace')

# --- PHP ---
try:
    html = get('https://windows.php.net/download/')
    # links like php-8.3.xx-nts-Win32-vs16-x64.zip
    cands = re.findall(r'href="(https?://[^"]*php-8\.3\.\d+-nts-Win32-vs16-x64\.zip)"', html)
    if not cands:
        cands = re.findall(r'href="(/downloads/releases/[^"]*php-8\.3\.\d+-nts-Win32-vs16-x64\.zip)"', html)
        cands = ['https://windows.php.net' + c for c in cands]
    print('PHP 8.3 nts x64 candidates:')
    for c in sorted(set(cands))[:5]:
        print('  ', c)
except Exception as e:
    print('PHP resolve FAIL:', type(e).__name__, e)

# --- MariaDB 11.4 winx64 zip ---
try:
    html = get('https://archive.mariadb.org/mariadb-11.4.x/winx64-packages/')
    m = re.findall(r'href="(mariadb-11\.4\.\d+-winx64\.zip)"', html)
    print('MariaDB 11.4 winx64 zip:')
    for c in sorted(set(m))[-3:]:
        print('  https://archive.mariadb.org/mariadb-11.4.x/winx64-packages/' + c)
    if not m:
        print('  (none matched; html len=%d)' % len(html))
except Exception as e:
    print('MariaDB resolve FAIL:', type(e).__name__, e)
