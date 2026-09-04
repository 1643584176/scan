# -*- coding: utf-8 -*-
import re, io

txt = io.open('_run_v103_out.txt', encoding='utf-8', errors='replace').read()
last = None
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    if 'V103C_DONE' in d and 'celld hits' in d:
        last = d
if last:
    i = last.find('=== N1 celld strings')
    j = last.find('V103C_DONE')
    print(last[i:j if j > i else i + 9000])
