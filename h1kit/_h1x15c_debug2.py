# -*- coding: utf-8 -*-
"""h1x15c: 逐步正则调试"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
pat1 = r'"(?:\\n\s*)?(?:query|mutation)\s+([A-Za-z0-9_]+)'
m = re.search(pat1, t)
print('pat1:', bool(m), m.group(1) if m else None)

pat2 = r'"(?:\\n\s*)?(?:query|mutation)\s+([A-Za-z0-9_]+)\(([^"]*?)\)'
m = re.search(pat2, t)
print('pat2:', bool(m), m.groups() if m else None)

pat3 = r'"(?:\\n\s*)?(?:query|mutation)\s+([A-Za-z0-9_]+)\([^"]*?\)\s*\{'
m = re.search(pat3, t)
print('pat3:', bool(m))

pat4 = r'"(?:\\n\s*)?(?:query|mutation)\s+([A-Za-z0-9_]+)'
cnt = 0
for mm in re.finditer(pat4, t):
    cnt += 1
    if cnt <= 3:
        print('sample:', mm.group(1), repr(t[mm.end():mm.end()+60]))
print('pat1 total:', cnt)
