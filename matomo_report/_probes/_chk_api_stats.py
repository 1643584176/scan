# -*- coding: utf-8 -*-
"""Sanity check: count API methods total vs with-check vs db-only, sample a few."""
import os
import re

ROOT = r'F:\scan\matomo_report\_src\matomo\plugins'
RX_FN = re.compile(r'public function (\w+)\s*\([^)]*\)\s*\{')
CHECKS = re.compile(r'checkUser|checkAdmin|Access::|Piwik::check|isUserHas|access\)|Access\(\)')

total = 0
with_check = 0
sample_no = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in {'.git', 'node_modules', 'tests', 'vendor', 'Updates', 'docs', 'lang'}]
    for fn in fns:
        if not fn.endswith('API.php'):
            continue
        p = os.path.join(dp, fn)
        src = open(p, encoding='utf-8', errors='replace').read()
        rel = os.path.relpath(p, r'F:\scan\matomo_report\_src\matomo')
        for m in RX_FN.finditer(src):
            start = m.start()
            i = src.find('{', start)
            depth = 0
            j = i
            while j < len(src) and j < i + 20000:
                c = src[j]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = src[i:j + 1]
            if len(body) > 18000:
                continue
            total += 1
            if CHECKS.search(body):
                with_check += 1
            else:
                line = src.count('\n', 0, start) + 1
                if len(sample_no) < 60:
                    sample_no.append('%s:%d %s' % (rel, line, m.group(1)))

print('total public methods (bounded):', total)
print('with check keywords:', with_check)
print('without:', total - with_check)
print()
for s in sample_no:
    print('NOCHECK:', s)
