# -*- coding: utf-8 -*-
"""Locate and print key functions in TableLogAction.php (python-based, gitbash-safe)."""
import re

p = r'F:\scan\matomo_report\_src\matomo\core\Tracker\TableLogAction.php'
src = open(p, encoding='utf-8', errors='replace').read()
print('file lines:', src.count('\n'))

for fname in ['getIdActionFromSegment', 'getOptimizedIdActionSqlMatch', 'getIdActionSqlMatch']:
    idx = src.find('function ' + fname)
    if idx == -1:
        print('NOT FOUND:', fname)
        continue
    # find end of function (next 'function ' at same indent or EOF)
    rest = src[idx + len(fname):]
    nxt = re.search(r'\n    (public|protected|private) function ', rest)
    end = idx + len(fname) + (nxt.start() if nxt else len(rest))
    body = src[idx:end]
    print('=' * 30, fname, '(%d chars)' % len(body))
    print(body[:4000])
