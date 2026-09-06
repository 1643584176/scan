# -*- coding: utf-8 -*-
"""Find public API methods lacking access checks (potential IDOR).

Heuristic: in plugins/*/API.php, public function methods that contain SQL/DB
calls or model calls but no checkUser*/Access::check* calls inside.
"""
import os
import re

ROOT = r'F:\scan\matomo_report\_src\matomo\plugins'
CHECKS = re.compile(r'checkUser|checkAdmin|Access::|Piwik::check|isUserHas|Access::getInstance\(\)->check')
RX_FN = re.compile(r'public function (\w+)\s*\(([^)]*)\)\s*\{')

results = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in {'.git', 'node_modules', 'tests', 'vendor', 'Updates', 'docs', 'lang'}]
    for fn in fns:
        if not (fn == 'API.php' or fn.endswith('API.php')):
            continue
        p = os.path.join(dp, fn)
        src = open(p, encoding='utf-8', errors='replace').read()
        rel = os.path.relpath(p, r'F:\scan\matomo_report\_src\matomo')
        for m in RX_FN.finditer(src):
            start = m.start()
            depth = 0
            i = src.find('{', start)
            j = i
            while j < len(src) and j < i + 30000:
                c = src[j]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = src[i:j + 1]
            if len(body) > 25000:
                continue
            has_db = re.search(r'Model\(|->getDb\(|Db::|fetchAll|fetchOne|query\(', body)
            has_check = CHECKS.search(body)
            if has_db and not has_check:
                line = src.count('\n', 0, start) + 1
                results.append((rel, line, m.group(1), len(body)))

print('public API methods with DB/model calls but NO visible access check: %d' % len(results))
for rel, line, fn, blen in sorted(results):
    print('%-70s @%-5d %-40s (%d bytes)' % (rel, line, fn, blen))
