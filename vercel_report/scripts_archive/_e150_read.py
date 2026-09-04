# -*- coding: utf-8 -*-
"""读 e150 行 185-215 完整内容 (J544-J558)"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

for i in range(185, 216):
    if i < len(lines):
        print('%4d: %s' % (i, lines[i][:1500]))
        print()
