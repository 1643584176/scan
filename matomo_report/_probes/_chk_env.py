# -*- coding: utf-8 -*-
"""Check local runtime availability: php / docker / mysql / xampp / phpstudy."""
import os
import shutil

print('PATH tools:')
for t in ('php', 'php.exe', 'docker', 'docker.exe', 'mysql', 'mysqld', 'composer'):
    print('  %-12s %s' % (t, shutil.which(t) or '-'))

cands = [
    r'C:\Program Files\Docker',
    r'C:\Program Files\PHP',
    r'C:\php',
    r'D:\php',
    r'C:\xampp',
    r'D:\xampp',
    r'C:\phpstudy_pro',
    r'D:\phpstudy_pro',
    r'C:\wamp64',
    r'D:\wamp64',
    r'C:\laragon',
    r'D:\laragon',
    r'C:\tools',
    r'D:\tools',
]
print('install dirs:')
for c in cands:
    if os.path.isdir(c):
        try:
            sub = sorted(os.listdir(c))[:8]
        except OSError:
            sub = []
        print('  [x] %s -> %s' % (c, sub))
    else:
        print('  [ ] %s' % c)

# search a bit for php.exe in common drive roots (depth 2)
import itertools
for drive in ('C:\\', 'D:\\', 'F:\\'):
    base = drive
    if not os.path.isdir(base):
        continue
    try:
        entries = sorted(os.listdir(base))
    except OSError:
        continue
    for e in entries:
        if 'php' in e.lower() or 'xampp' in e.lower() or 'wamp' in e.lower() or 'laragon' in e.lower() or 'study' in e.lower():
            print('  found-like:', drive + e)
