# -*- coding: utf-8 -*-
"""_api_doc.md 中 api_keys / org api_keys 定义提取"""
import re, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_api_doc.md')
s = open(p, encoding='utf-8', errors='replace').read()
print('size:', len(s), flush=True)
idxs = [m.start() for m in re.finditer(r'api_keys', s)]
print('occurrences:', len(idxs), flush=True)
for i in idxs[:14]:
    seg = s[max(0, i - 300):i + 500].replace('\n', ' ')
    print('---', flush=True)
    print(seg[:800], flush=True)
