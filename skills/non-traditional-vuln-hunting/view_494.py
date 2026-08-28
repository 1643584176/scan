# -*- coding: utf-8 -*-
"""查看 494b74ea 会话全文"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\scan\skills\non-traditional-vuln-hunting\494b74ea_text.txt', encoding='utf-8') as f:
    lines = f.readlines()
for i, t in enumerate(lines):
    print('%3d: %s' % (i, t.strip()[:500]))
