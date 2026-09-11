# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
fn = 'Figma-SQL注入-r214-218-极限深挖-结论-2026-09-11.md'
t = open(fn, encoding='utf-8').read()
ls = t.splitlines()
print('TOTAL', len(ls))
for i, l in enumerate(ls[-40:], start=len(ls) - 40):
    print(i + 1, ':', l[:120])
