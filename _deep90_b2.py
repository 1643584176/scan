# -*- coding: utf-8 -*-
"""直接打印 deep90 输出中的 BODY 段落"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\out\deep33090_guest_20260829_134434.txt', 'rb').read().decode('utf-8', errors='replace')
data2 = data.replace('\\n', '\n').replace('\\r', '')

lines = data2.splitlines()
for i, ln in enumerate(lines):
    if 'BODY' in ln or 'cert ' in ln and 'subject' in ln:
        print('=== %d ===' % i)
        print(ln[:4000])
        print()
