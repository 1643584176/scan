# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
txt = open('_q40_out.txt', encoding='utf-8', errors='replace').read()
print('=== _q40_out.txt 中 frequenc* 上下文 ===')
for m in re.finditer(r'.{60}[Ff]requenc.{120}', txt):
    print(repr(m.group(0)))
    print('---')
print()
src = open('_q40_notif_chain.py', encoding='utf-8', errors='replace').read()
print('=== _q40_notif_chain.py 中 frequenc* 行 ===')
for i, line in enumerate(src.splitlines(), 1):
    if 'requenc' in line:
        print(i, line[:160])
