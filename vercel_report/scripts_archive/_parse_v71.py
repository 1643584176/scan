# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
txt = open(r'D:\scan\v71_run.log', encoding='utf-8', errors='replace').read()
out = []
for m in re.finditer(r'\[1788148\d+\.\d{3}\] ([^\n]{0,300})', txt):
    out.append(m.group(1))
seen = set()
for x in out:
    if x not in seen:
        seen.add(x)
        print(x[:300])
