# -*- coding: utf-8 -*-
import re
data = open(r'D:\scan\_run_v183_out.txt', encoding='utf-8', errors='replace').read()
m = re.search(r'TCP LISTEN[^"]{0,6000}', data)
if m:
    print(m.group(0).replace('\\n', '\n')[:6000])
