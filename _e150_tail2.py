# -*- coding: utf-8 -*-
"""提取 e150 会话 292-311 行完整内容 (V17-V29)"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()
for i in range(292, min(311, len(lines))):
    print('%4d: %s' % (i, lines[i][:900]))
    print()
