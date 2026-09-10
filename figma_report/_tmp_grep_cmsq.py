# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = io.open('_r62_out.txt', encoding='utf-8', errors='replace').read()
print('TOTAL', len(t))
for ln in t.split('\n'):
    low = ln.lower()
    if ('collection' in low or 'cms' in low or 'items' in low) and ('sort' in low or 'filter' in low or 'search' in low or 'where' in low):
        print(ln[:560])
        print('---')
print('DONE')
