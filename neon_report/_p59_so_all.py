# -*- coding: utf-8 -*-
"""prod_app.js: so 全部出现位置分析"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []
idxs = [m.start() for m in re.finditer(r'\bso\b', src)]
out.append('total so occurrences: %d' % len(idxs))
for i in idxs[:40]:
    seg = src[max(0, i - 120):i + 120].replace('\n', ' ')
    out.append('@%d: %s' % (i, seg[:230]))
open(os.path.join(here, '_p59_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
