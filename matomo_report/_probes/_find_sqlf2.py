# -*- coding: utf-8 -*-
"""Enumerate sqlFilter/sqlFilterValue definitions in 5.x Dimension model."""
import os
import re

ROOT = r'F:\scan\matomo_report\_src\matomo\core'
ROOT2 = r'F:\scan\matomo_report\_src\matomo\plugins'

RX_SET = re.compile(r"setSqlFilter(Value)?\s*\(\s*(\[[^\]]*\]|function|[^)]*)\)", re.S)
RX_PROP = re.compile(r"function getSqlFilter(Value)?\s*\(")
RX_CALL = re.compile(r"->getSqlFilter(Value)?\s*\(")

def scan(base):
    out = []
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d not in {'.git', 'node_modules', 'tests', 'vendor', 'Updates'}]
        for fn in fns:
            if not fn.endswith('.php'):
                continue
            p = os.path.join(dp, fn)
            try:
                src = open(p, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            rel = os.path.relpath(p, r'F:\scan\matomo_report\_src\matomo')
            for name, rx in (('setSqlFilter', RX_SET), ('getSqlFilter', RX_PROP)):
                for m in rx.finditer(src):
                    line = src.count('\n', 0, m.start()) + 1
                    snip = src[m.start():m.start() + 100].replace('\n', ' ')
                    out.append('%s:%d %s' % (rel, line, snip[:95]))
    return out

hits = scan(ROOT) + scan(ROOT2)
print('total hits:', len(hits))
seen = set()
for h in hits:
    if h in seen:
        continue
    seen.add(h)
    print(h)
