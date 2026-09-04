# -*- coding: utf-8 -*-
import re
data = open(r'D:\scan\_run_v183_out.txt', encoding='utf-8', errors='replace').read()
for m in re.finditer(r'26661', data):
    s = max(0, m.start() - 250)
    e = min(len(data), m.end() + 300)
    print('---')
    print(data[s:e].replace('\\n', '\n')[:650])
    print()
