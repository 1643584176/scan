# -*- coding: utf-8 -*-
"""Dump CustomDimensions DAO query functions (check for raw interpolation)."""
import re

p = r'F:\scan\matomo_report\_src\matomo\plugins\CustomDimensions\Dao\Configuration.php'
src = open(p, encoding='utf-8', errors='replace').read()
print('lines:', src.count('\n'))
rx_fn = re.compile(r'(public|protected|private) function (\w+)\s*\([^)]*\)\s*\{')
for m in rx_fn.finditer(src):
    start = m.start()
    depth = 0
    i = src.find('{', start)
    j = i
    while j < len(src):
        c = src[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    body = src[i:j + 1]
    if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', body, re.I) and '$' in body:
        line = src.count('\n', 0, start) + 1
        print('\n===== %s() @%d =====' % (m.group(2), line))
        print(body[:2200])
