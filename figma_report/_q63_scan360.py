# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for fn in ['Figma-SQL注入-r214-218-极限深挖-结论-2026-09-11.md', 'Figma-SQL注入总账-2026-09-10.md']:
    print(f'\n######## {fn}')
    t = open(fn, encoding='utf-8').read()
    ls = t.splitlines()
    print('TOTAL', len(ls))
    for i, l in enumerate(ls, 1):
        if '360' in l or '30 波' in l or '30波' in l:
            print(f'  {i}: {l[:130]}')
    print('--- tail 8 ---')
    for i, l in enumerate(ls[-8:], start=len(ls) - 8):
        print(i + 1, ':', l[:130])
