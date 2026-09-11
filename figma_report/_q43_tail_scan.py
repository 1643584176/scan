# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
txt = open('Figma-SQL注入总账-2026-09-10.md', encoding='utf-8').read()
lines = txt.splitlines()
print('total', len(lines))
for i, l in enumerate(lines[-25:], len(lines) - 24):
    print(i, '|', l)
