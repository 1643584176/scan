# -*- coding: utf-8 -*-
"""Enumerate API methods on the RELEASE tree (5.13.0) with/without access checks."""
import os
import re
import json

ROOT = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins'
RX_FN = re.compile(r'public function (\w+)\s*\(([^)]*)\)\s*\{')
CHECKS = re.compile(r'checkUser|checkAdmin|Access::|Piwik::check|isUserHas|->access\)|Access\(\)|checkTokenAuthIsNotAnonymous')

out = {}
total = with_check = 0
nocheck = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in {'.git', 'node_modules', 'tests', 'vendor', 'Updates', 'docs', 'lang', 'vue', 'stylesheets', 'javascripts', 'templates'}]
    for fn in fns:
        if not fn.endswith('API.php'):
            continue
        p = os.path.join(dp, fn)
        src = open(p, encoding='utf-8', errors='replace').read()
        rel = os.path.relpath(p, r'F:\scan\matomo_report\_src\matomo-release\matomo')
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
            # exclude constructor-ish and private called (isApiMethod not known) - keep all public
            if CHECKS.search(body):
                with_check += 1
            else:
                line = src.count('\n', 0, start) + 1
                params = re.sub(r'\s+', ' ', m.group(2))[:120]
                nocheck.append({'file': rel, 'line': line, 'method': m.group(1),
                                'params': params, 'body_len': len(body)})

print('total:', total, 'with_check:', with_check, 'nocheck:', len(nocheck))
json.dump(nocheck, open(r'F:\scan\matomo_report\_probes\_nocheck_methods.json', 'w'),
          indent=1, ensure_ascii=False)
# top-level sample by plugin
from collections import Counter
c = Counter(x['file'].split('\\')[1] for x in nocheck)
print('by plugin:', dict(c))
for x in nocheck[:25]:
    print('NOCHECK:', x['file'].split('\\')[1], x['method'], '|', x['params'][:90])
