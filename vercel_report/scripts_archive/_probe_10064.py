# -*- coding: utf-8 -*-
import re
for fn in [r'D:\scan\_run_v171_out.txt', r'D:\scan\_run_v174_out.txt', r'D:\scan\_run_v180_out.txt']:
    data = open(fn, encoding='utf-8', errors='replace').read()
    print('=====', fn)
    seen = set()
    for m in re.finditer(r'100\.64\.1\.\d+[^\s"\\]{0,60}', data):
        seg = m.group(0)
        if seg not in seen:
            seen.add(seg)
            print(' ', seg[:100])
