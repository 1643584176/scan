# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: np 全部 9 次出现上下文"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []
for m in re.finditer(r'\bnp\b', src):
    i = m.start()
    seg = src[max(0, i - 300):i + 300].replace('\n', ' ')
    out.append('@%d: %s' % (i, seg[:550]))
open(os.path.join(here, '_p75_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
