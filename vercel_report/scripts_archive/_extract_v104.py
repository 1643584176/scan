# -*- coding: utf-8 -*-
import re, io

txt = io.open('_run_v104_out.txt', encoding='utf-8', errors='replace').read()
last = None
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    if 'V104C_DONE' in d:
        last = d
if last:
    i = last.find('=== P1 23456 grpc')
    j = last.find('V104C_DONE')
    print(last[i:j if j > i else i + 9000])
