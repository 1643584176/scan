# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
for fn in [r'D:\scan\_run_v191_out.txt', r'D:\scan\_run_v190_out.txt']:
    try:
        d = open(fn, 'rb').read().decode('utf-8', errors='replace')
    except Exception as e:
        print(fn, 'ERR', e)
        continue
    print('=====', fn, len(d))
    for m in re.finditer(r'CTRL [A-Z][A-Za-z0-9 _\-]*', d):
        print(repr(m.group(0)[:150]))
    for m in re.finditer(r'CELL [A-Z][A-Za-z0-9 _\-]*', d):
        print(repr(m.group(0)[:150]))
