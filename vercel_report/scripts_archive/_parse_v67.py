# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
txt = open(r'D:\scan\v67_run.log', encoding='utf-8', errors='replace').read()
for m in re.finditer(r'\[1788148\d+\.\d{3}\] ([^\n]{0,400})', txt):
    print(m.group(1)[:400])
