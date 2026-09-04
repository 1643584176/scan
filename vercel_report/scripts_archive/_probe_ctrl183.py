# -*- coding: utf-8 -*-
import re
data = open(r'D:\scan\_run_v183_out.txt', encoding='utf-8', errors='replace').read()
for m in re.finditer(r'CTRL[^\\\\]*', data):
    print(repr(m.group(0))[:200])
