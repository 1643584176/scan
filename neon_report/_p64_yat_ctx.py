# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js @1869725 前后 6000 字符完整提取(class yat API client)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []
i = 1869725
out.append(src[i - 2500:i + 4500])
open(os.path.join(here, '_p64_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done', flush=True)
