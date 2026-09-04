# -*- coding: utf-8 -*-
"""prod_app.js @13316 import 行完整提取(找 ag/so 的源文件)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []
# import 段起止
i = 13316
seg = src[max(0, i - 2000):i + 1500]
out.append(seg)
open(os.path.join(here, '_p60_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done', flush=True)
