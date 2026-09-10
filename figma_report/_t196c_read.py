# -*- coding: utf-8 -*-
import io
print('===== c8 UserProfilePageView err')
print(io.open('_r196c_c8.json', encoding='utf-8', errors='replace').read()[:1400])
print()
print('===== c6 OneItemView blocks')
big = io.open('_r196c_c6.json', encoding='utf-8', errors='replace').read()
lines = big.split('\n')
for i, l in enumerate(lines[:6]):
    print(f'L{i} len={len(l)}: {l[:320]!r}')
print('L8:', lines[8][:220] if len(lines) > 8 else 'NA')
print('DONE')
