# -*- coding: utf-8 -*-
import re
data = open(r'D:\scan\_run_v184_out.txt', encoding='utf-8', errors='replace').read()
for m in re.finditer(r'26661', data):
    s = max(0, m.start() - 200)
    e = min(len(data), m.end() + 250)
    seg = data[s:e].replace('\\n', '\n')
    print('---')
    print(seg[:520])
    print()
