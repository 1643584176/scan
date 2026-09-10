# -*- coding: utf-8 -*-
# r196t 判读2: 精读 t1/t4/t7/t8/t12 全文
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for f in ['_r196t_t1.json', '_r196t_t4.json', '_r196t_t7.json', '_r196t_t8.json', '_r196t_t12.json']:
    b = io.open(f, encoding='utf-8', errors='replace').read()
    print('=' * 28, f, len(b))
    print(b)
    print()
