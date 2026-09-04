# -*- coding: utf-8 -*-
import re
for fn in [r'D:\scan\_run_v171_out.txt', r'D:\scan\_run_v174_out.txt', r'D:\scan\_run_v180_out.txt']:
    data = open(fn, encoding='utf-8', errors='replace').read()
    print('=====', fn)
    for m in re.finditer(r'100\.64\.1', data):
        s = max(0, m.start() - 120)
        e = min(len(data), m.end() + 200)
        print('---')
        print(data[s:e].replace('\\n', '\n')[:380])
        print()
