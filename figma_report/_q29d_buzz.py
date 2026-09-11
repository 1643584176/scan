# -*- coding: utf-8 -*-
import io, re, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')
t = io.open('_figma_r196e_reqid.py', encoding='utf-8', errors='replace').read()
print('=== buzz 相关行 ===')
for ln in t.splitlines():
    if 'buzz' in ln.lower():
        print(ln)
print()
print('=== 所有 /api/ 路径 ===')
for m in re.finditer(r"['\"](/api/[^'\"]{2,120})['\"]", t):
    print(m.group(1))
