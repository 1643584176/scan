# -*- coding: utf-8 -*-
"""Check .gitignore full content + probe dir file types."""
ROOT = 'F:/scan'
lines = open(ROOT + '/.gitignore', encoding='utf-8', errors='replace').read().splitlines()
for i, l in enumerate(lines, 1):
    print(i, repr(l))
