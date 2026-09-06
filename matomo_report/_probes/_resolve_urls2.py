# -*- coding: utf-8 -*-
"""Resolve real download URLs - directory listing approach."""
import re
import urllib.request

def get(url, max_bytes=3_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 h1kit/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(max_bytes).decode('utf-8', 'replace')

# --- PHP releases listing ---
try:
    html = get('https://windows.php.net/downloads/releases/')
    zips = re.findall(r'href="(php-8\.\d+\.\d+-nts-Win32-vs\d+-x64\.zip)"', html)
    print('PHP nts x64 zips on releases page:')
    for c in sorted(set(zips))[-8:]:
        print('  https://windows.php.net/downloads/releases/' + c)
    if not zips:
        print('  none; page len', len(html))
except Exception as e:
    print('PHP FAIL:', type(e).__name__, e)

# --- MariaDB versions index ---
try:
    html = get('https://archive.mariadb.org/')
    vers = re.findall(r'href="(mariadb-11\.4\.\d+)/"', html)
    print('MariaDB 11.4.x versions:', sorted(set(vers)))
except Exception as e:
    print('MariaDB index FAIL:', type(e).__name__, e)
