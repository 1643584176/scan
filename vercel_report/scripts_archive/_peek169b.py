# -*- coding: utf-8 -*-
import re
data = open('skills/non-traditional-vuln-hunting/vda169_probe_guest.py', encoding='utf-8', errors='replace').read()
for kw in ['init.sock', 'JSON']:
    for m in re.finditer(kw, data):
        s = max(0, m.start() - 300)
        e = min(len(data), m.end() + 500)
        print('=== %s @%d ===' % (kw, m.start()))
        print(data[s:e])
        print()
