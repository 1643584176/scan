# -*- coding: utf-8 -*-
import re, io

txt = io.open('_run_v102_out.txt', encoding='utf-8', errors='replace').read()
last = None
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    if 'M3 host bin' in d:
        last = d
if last:
    i = last.find('=== M3 host bin')
    j = last.find('V102C_DONE')
    print(last[i:j if j > i else i + 8000])
