# -*- coding: utf-8 -*-
"""Find sqlFilter / sqlFilterValue callback definitions and SegmentsList registrations."""
import os
import re

ROOT = r'F:\scan\matomo_report\_src\matomo'
SKIP = {'.git', 'node_modules', 'js', 'lang', 'libs', 'vendor', 'tests', 'misc', '.github', 'config'}

PATS = [
    ("sqlFilter =>", re.compile(r"sqlFilter\s*=>\s*'([^']+)'|sqlFilter\s*=>\s*\[([^\]]+)\]|sqlFilter\s*=>\s*function")),
    ("sqlFilterValue =>", re.compile(r"sqlFilterValue\s*=>\s*'([^']+)'")),
    ("call_user_func", re.compile(r"call_user_func\s*\([^)]*\)")),
    ("SegmentsList::get()->add", re.compile(r"addSegment|SegmentsList::get\(\)->add")),
]

hits = {k: [] for k, _ in PATS}

def walk():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP]
        for fn in fns:
            if fn.endswith('.php'):
                yield os.path.join(dp, fn)

for p in walk():
    rel = os.path.relpath(p, ROOT)
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            src = f.read()
    except OSError:
        continue
    for name, rx in PATS:
        for m in rx.finditer(src):
            line_no = src.count('\n', 0, m.start()) + 1
            snippet = src[m.start():m.start() + 120].replace('\n', ' ')
            hits[name].append('%s:%d %s' % (rel, line_no, snippet[:110]))

for name, items in hits.items():
    print('==== %s (%d) ====' % (name, len(items)))
    for it in items[:25]:
        print('  ', it)
    if len(items) > 25:
        print('   ... %d more' % (len(items) - 25))
